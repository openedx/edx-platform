"""
Course API Views
"""
from completion.exceptions import UnavailableCompletionData
from completion.utilities import get_key_to_last_completed_block
from django.conf import settings
from django.utils.functional import cached_property
from edx_django_utils.cache import TieredCache
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
from xmodule.modulestore.search import path_to_location
from xmodule.x_module import PUBLIC_VIEW, STUDENT_VIEW

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.util.views import expose_header
from lms.djangoapps.edxnotes.helpers import is_feature_enabled
from lms.djangoapps.certificates.api import get_certificate_url
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.course_api.api import course_detail
from lms.djangoapps.course_goals.models import UserActivity
from lms.djangoapps.course_goals.api import get_course_goal
from lms.djangoapps.courseware.access import has_access

from lms.djangoapps.courseware.context_processor import user_timezone_locale_prefs
from lms.djangoapps.courseware.entrance_exams import course_has_entrance_exam, user_has_passed_entrance_exam
from lms.djangoapps.courseware.masquerade import (
    is_masquerading_as_specific_student,
    setup_masquerade,
    is_masquerading_as_non_audit_enrollment,
)
from lms.djangoapps.courseware.models import LastSeenCoursewareTimezone
from lms.djangoapps.courseware.module_render import get_module_by_usage_id
from lms.djangoapps.courseware.toggles import course_exit_page_is_active
from lms.djangoapps.courseware.views.views import get_cert_data
from lms.djangoapps.gating.api import get_entrance_exam_score, get_entrance_exam_usage_key
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.agreements.api import get_integrity_signature
from openedx.core.djangoapps.courseware_api.utils import get_celebrations_dict
from openedx.core.djangoapps.programs.utils import ProgramProgressMeter
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin
from openedx.core.lib.courses import get_course_by_id
from openedx.features.course_experience import DISPLAY_COURSE_SOCK_FLAG
from openedx.features.course_experience import ENABLE_COURSE_GOALS
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_duration_limits.access import get_access_expiration_data
from openedx.features.discounts.utils import generate_offer_data
from common.djangoapps.student.models import (
    CourseEnrollment,
    CourseEnrollmentCelebration,
    LinkedInAddToProfileConfiguration
)

from .serializers import CourseInfoSerializer


class CoursewareMeta:
    """
    Encapsulates courseware and enrollment metadata.
    """

    def __init__(self, course_key, request, username=''):
        self.request = request
        self.overview = course_detail(
            self.request,
            username or self.request.user.username,
            course_key,
        )

        original_user_is_staff = has_access(self.request.user, 'staff', self.overview).has_access
        self.original_user_is_global_staff = self.request.user.is_staff
        self.course_key = course_key
        self.course = get_course_by_id(self.course_key)
        self.course_masquerade, self.effective_user = setup_masquerade(
            self.request,
            course_key,
            staff_access=original_user_is_staff,
        )
        self.request.user = self.effective_user
        self.enrollment_object = CourseEnrollment.get_enrollment(self.effective_user, self.course_key,
                                                                 select_related=['celebration', 'user__celebration'])

    def __getattr__(self, name):
        return getattr(self.overview, name)

    @property
    def enrollment(self):
        """
        Return enrollment information.
        """
        if self.effective_user.is_anonymous or not self.enrollment_object:
            mode = None
            is_active = False
        else:
            mode = self.enrollment_object.mode
            is_active = self.enrollment_object.is_active
        return {'mode': mode, 'is_active': is_active}

    @property
    def access_expiration(self):
        return get_access_expiration_data(self.effective_user, self.overview)

    @property
    def offer(self):
        return generate_offer_data(self.effective_user, self.overview)

    @property
    def content_type_gating_enabled(self):
        return ContentTypeGatingConfig.enabled_for_enrollment(
            user=self.effective_user,
            course_key=self.course_key,
        )

    @property
    def can_show_upgrade_sock(self):
        return DISPLAY_COURSE_SOCK_FLAG.is_enabled(self.course_key)

    @property
    def license(self):
        return self.course.license

    @property
    def notes(self):
        """
        Return whether edxnotes is enabled and visible.
        """
        return {
            'enabled': is_feature_enabled(self.overview, self.effective_user),
            'visible': self.overview.edxnotes_visibility,
        }

    @property
    def celebrations(self):
        """
        Returns a dict of celebrations that should be performed.
        """
        browser_timezone = self.request.query_params.get('browser_timezone', None)
        celebrations = get_celebrations_dict(self.effective_user, self.enrollment_object, self.course, browser_timezone)
        return celebrations

    @property
    def course_goals(self):
        """
        Returns a dict of course goals
        """
        course_goals = {
            'selected_goal': None,
            'weekly_learning_goal_enabled': False,
        }
        user_is_enrolled = CourseEnrollment.is_enrolled(self.effective_user, self.course_key)
        if (user_is_enrolled and ENABLE_COURSE_GOALS.is_enabled(self.course_key)):
            course_goals['weekly_learning_goal_enabled'] = True
            selected_goal = get_course_goal(self.effective_user, self.course_key)
            if selected_goal:
                course_goals['selected_goal'] = {
                    'days_per_week': selected_goal.days_per_week,
                    'subscribed_to_reminders': selected_goal.subscribed_to_reminders,
                }
        return course_goals

    @cached_property
    def course_grade(self):
        """
        Returns the Course Grade for the effective user in the course

        Cached property since we use this twice in the class and don't want to recreate the entire grade.
        """
        return CourseGradeFactory().read(self.effective_user, self.course)

    @property
    def user_has_passing_grade(self):
        """ Returns a boolean on if the effective_user has a passing grade in the course """
        if not self.effective_user.is_anonymous:
            user_grade = self.course_grade.percent
            return user_grade >= self.course.lowest_passing_grade
        return False

    @property
    def course_exit_page_is_active(self):
        """ Returns a boolean on if the course exit page is active """
        return course_exit_page_is_active(self.course_key)

    @property
    def certificate_data(self):
        """
        Returns certificate data if the effective_user is enrolled.
        Note: certificate data can be None depending on learner and/or course state.
        """
        if self.enrollment_object:
            return get_cert_data(self.effective_user, self.course, self.enrollment_object.mode)

    @property
    def entrance_exam_data(self):
        """
        Returns Entrance Exam data for the course

        Although some of the fields will have values (i.e. entrance_exam_minimum_score_pct and
        entrance_exam_passed), nothing will be used unless entrance_exam_enabled is True.
        """
        return {
            'entrance_exam_current_score': get_entrance_exam_score(
                self.course_grade, get_entrance_exam_usage_key(self.overview),
            ),
            'entrance_exam_enabled': course_has_entrance_exam(self.overview),
            'entrance_exam_id': self.overview.entrance_exam_id,
            'entrance_exam_minimum_score_pct': self.overview.entrance_exam_minimum_score_pct,
            'entrance_exam_passed': user_has_passed_entrance_exam(self.effective_user, self.overview),
        }

    @property
    def verify_identity_url(self):
        """
        Returns a String to the location to verify a learner's identity
        Note: This might return an absolute URL (if the verification MFE is enabled) or a relative
            URL. The serializer will make the relative URL absolute so any consumers can treat this
            as a full URL.
        """
        if self.enrollment_object and self.enrollment_object.mode in CourseMode.VERIFIED_MODES:
            verification_status = IDVerificationService.user_status(self.effective_user)['status']
            if verification_status == 'must_reverify':
                return IDVerificationService.get_verify_location()
            else:
                return IDVerificationService.get_verify_location(self.course_key)

    @property
    def verification_status(self):
        """
        Returns a String of the verification status of learner.
        """
        if self.enrollment_object and self.enrollment_object.mode in CourseMode.VERIFIED_MODES:
            return IDVerificationService.user_status(self.effective_user)['status']
        # I know this looks weird (and is), but this is just so it is inline with what the
        # IDVerificationService.user_status method would return before a verification was created
        return 'none'

    @property
    def linkedin_add_to_profile_url(self):
        """
        Returns a URL to add a certificate to a LinkedIn profile (will autofill fields).

        Requires LinkedIn sharing to be enabled, either via a site configuration or a
        LinkedInAddToProfileConfiguration object being enabled.
        """
        if self.effective_user.is_anonymous:
            return

        linkedin_config = LinkedInAddToProfileConfiguration.current()
        if linkedin_config.is_enabled():
            try:
                user_certificate = GeneratedCertificate.eligible_certificates.get(
                    user=self.effective_user, course_id=self.course_key
                )
            except GeneratedCertificate.DoesNotExist:
                return
            cert_url = self.request.build_absolute_uri(
                get_certificate_url(course_id=self.course_key, uuid=user_certificate.verify_uuid)
            )
            return linkedin_config.add_to_profile_url(
                self.overview.display_name, user_certificate.mode, cert_url, certificate=user_certificate,
            )

    @property
    def is_integrity_signature_enabled(self):
        """
        Django setting for the integrity signature feature.
        """
        return settings.FEATURES.get('ENABLE_INTEGRITY_SIGNATURE', False)

    @property
    def user_needs_integrity_signature(self):
        """
        Boolean describing whether the user needs to sign the integrity agreement for a course.
        """
        if not settings.FEATURES.get('ENABLE_INTEGRITY_SIGNATURE'):
            return False

        integrity_signature_required = (
            self.enrollment_object
            # Master's enrollments are excluded here as honor code is handled separately
            and self.enrollment_object.mode in CourseMode.CREDIT_MODES + CourseMode.CREDIT_ELIGIBLE_MODES
        )

        if not integrity_signature_required:
            # Check masquerading as a non-audit enrollment
            integrity_signature_required = is_masquerading_as_non_audit_enrollment(
                self.effective_user,
                self.course_key,
                self.course_masquerade
            )

        if integrity_signature_required:
            signature = get_integrity_signature(self.effective_user.username, str(self.course_key))
            if not signature:
                return True

        return False

    @property
    def related_programs(self):
        """
        Returns related program data if the effective_user is enrolled.
        Note: related programs can be None depending on the course.
        """
        if self.effective_user.is_anonymous:
            return

        meter = ProgramProgressMeter(self.request.site, self.effective_user)
        inverted_programs = meter.invert_programs()
        related_programs = inverted_programs.get(str(self.course_key))

        if related_programs is None:
            return

        related_progress = meter.progress(programs=related_programs)
        progress_by_program = {
            progress['uuid']: progress for progress in related_progress
        }

        programs = [{
            'progress': progress_by_program[program['uuid']],
            'title': program['title'],
            'slug': program['type_attrs']['slug'],
            'url': program['detail_url'],
            'uuid': program['uuid']
        } for program in related_programs]

        return programs

    @property
    def user_timezone(self):
        """Returns the user's timezone setting (may be None)"""
        user_timezone_locale = user_timezone_locale_prefs(self.request)
        return user_timezone_locale['user_timezone']

    @property
    def can_access_proctored_exams(self):
        """Returns if the user is eligible to access proctored exams"""
        if is_masquerading_as_non_audit_enrollment(
            self.effective_user,
            self.course_key,
            self.course_masquerade
        ):
            # Masquerading should mimic the correct enrollment track behavior.
            return True
        else:
            enrollment_mode = self.enrollment['mode']
            enrollment_active = self.enrollment['is_active']
            return enrollment_active and CourseMode.is_eligible_for_certificate(enrollment_mode)


class CoursewareInformation(RetrieveAPIView):
    """
    **Use Cases**

        Request details for a course

    **Example Requests**

        GET /api/courseware/course/{course_key}

    **Response Values**

        Body consists of the following fields:

        * access_expiration: An object detailing when access to this course will expire
            * expiration_date: (str) When the access expires, in ISO 8601 notation
            * masquerading_expired_course: (bool) Whether this course is expired for the masqueraded user
            * upgrade_deadline: (str) Last chance to upgrade, in ISO 8601 notation (or None if can't upgrade anymore)
            * upgrade_url: (str) Upgrade linke (or None if can't upgrade anymore)
        * celebrations: An object detailing which celebrations to render
            * first_section: (bool) If the first section celebration should render
                Note: Also uses information from frontend so this value is not final
            * streak_length_to_celebrate: (int) The streak length to celebrate for the learner
            * streak_discount_enabled: (bool) If the frontend should render an upgrade discount for hitting the streak
            * weekly_goal: (bool) If the weekly goal celebration should render
        * course_goals:
            * selected_goal:
                * days_per_week: (int) The number of days the learner wants to learn per week
                * subscribed_to_reminders: (bool) Whether the learner wants email reminders about their goal
            * weekly_learning_goal_enabled: Flag indicating if this feature is enabled for this call
        * effort: A textual description of the weekly hours of effort expected
            in the course.
        * end: Date the course ends, in ISO 8601 notation
        * enrollment: Enrollment status of authenticated user
            * mode: `audit`, `verified`, etc
            * is_active: boolean
        * enrollment_end: Date enrollment ends, in ISO 8601 notation
        * enrollment_start: Date enrollment begins, in ISO 8601 notation
        * entrance_exam_data: An object containing information about the course's entrance exam
            * entrance_exam_current_score: (float) The users current score on the entrance exam
            * entrance_exam_enabled: (bool) If the course has an entrance exam
            * entrance_exam_id: (str) The block id for the entrance exam if enabled. Will be a section (chapter)
            * entrance_exam_minimum_score_pct: (float) The minimum score a user must receive on the entrance exam
                to unlock the remainder of the course. Returned as a float (i.e. 0.7 for 70%)
            * entrance_exam_passed: (bool) Indicates if the entrance exam has been passed
        * id: A unique identifier of the course; a serialized representation
            of the opaque key identifying the course.
        * media: An object that contains named media items.  Included here:
            * course_image: An image to show for the course.  Represented
              as an object with the following fields:
                * uri: The location of the image
        * name: Name of the course
        * offer: An object detailing upgrade discount information
            * code: (str) Checkout code
            * expiration_date: (str) Expiration of offer, in ISO 8601 notation
            * original_price: (str) Full upgrade price without checkout code; includes currency symbol
            * discounted_price: (str) Upgrade price with checkout code; includes currency symbol
            * percentage: (int) Amount of discount
            * upgrade_url: (str) Checkout URL
        * org: Name of the organization that owns the course
        * related_programs: A list of objects that contains program data related to the given course including:
            * progress: An object containing program progress:
                * complete: (int) Number of complete courses in the program (a course is completed if the user has
                    earned a certificate for any of the nested course runs)
                * in_progress: (int) Number of courses in the program that are in progress (a course is in progress if
                    the user has enrolled in any of the nested course runs)
                * not_started: (int) Number of courses in the program that have not been started
            * slug: (str) The program type
            * title: (str) The title of the program
            * url: (str) The link to the program's landing page
            * uuid: (str) A unique identifier of the program
        * short_description: A textual description of the course
        * start: Date the course begins, in ISO 8601 notation
        * start_display: Readably formatted start of the course
        * start_type: Hint describing how `start_display` is set. One of:
            * `"string"`: manually set by the course author
            * `"timestamp"`: generated from the `start` timestamp
            * `"empty"`: no start date is specified
        * pacing: Course pacing. Possible values: instructor, self
        * user_timezone: User's chosen timezone setting (or null for browser default)
        * user_has_passing_grade: Whether or not the effective user's grade is equal to or above the courses minimum
            passing grade
        * course_exit_page_is_active: Flag for the learning mfe on whether or not the course exit page should display
        * certificate_data: data regarding the effective user's certificate for the given course
        * verify_identity_url: URL for a learner to verify their identity. Only returned for learners enrolled in a
            verified mode. Will update to reverify URL if necessary.
        * linkedin_add_to_profile_url: URL to add the effective user's certificate to a LinkedIn Profile.
        * user_needs_integrity_signature: Whether the user needs to sign the integrity agreement for the course

    **Parameters:**

        requested_fields (optional) comma separated list:
            If set, then only those fields will be returned.
        username (optional) username to masquerade as (if requesting user is staff)

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent or the username was not provided
          for an authenticated request.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    serializer_class = CourseInfoSerializer

    def set_last_seen_courseware_timezone(self, user):
        """
        The timezone in the user's account is frequently not set.
        This method sets a user's recent timezone that can be used as a fallback
        """
        if not user.id:
            return

        cache_key = 'browser_timezone_{}'.format(str(user.id))
        browser_timezone = self.request.query_params.get('browser_timezone', None)
        cached_value = TieredCache.get_cached_response(cache_key)
        if not cached_value.is_found:
            if browser_timezone:
                TieredCache.set_all_tiers(cache_key, str(browser_timezone), 86400)  # Refresh the cache daily
                LastSeenCoursewareTimezone.objects.update_or_create(
                    user=user,
                    defaults={'last_seen_courseware_timezone': browser_timezone},
                )

    def get_object(self):
        """
        Return the requested course object, if the user has appropriate
        permissions.
        """
        original_user = self.request.user
        if self.request.user.is_staff:
            username = self.request.GET.get('username', '') or self.request.user.username
        else:
            username = self.request.user.username
        course_key = CourseKey.from_string(self.kwargs['course_key_string'])
        overview = CoursewareMeta(
            course_key,
            self.request,
            username=username,
        )
        # Record course goals user activity for learning mfe courseware on web
        UserActivity.record_user_activity(self.request.user, course_key)

        # Record a user's browser timezone
        self.set_last_seen_courseware_timezone(original_user)

        return overview

    def get_serializer_context(self):
        """
        Return extra context to be used by the serializer class.
        """
        context = super().get_serializer_context()
        context['requested_fields'] = self.request.GET.get('requested_fields', None)
        return context

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Return the final response, exposing the 'Date' header for computing relative time to the dates in the data.

        Important dates such as 'access_expiration' are enforced server-side based on correct time; client-side clocks
        are frequently substantially far off which could lead to inaccurate messaging and incorrect expectations.
        Therefore, any messaging about those dates should be based on the server time and preferably in relative terms
        (time remaining); the 'Date' header is a straightforward and generalizable way for client-side code to get this
        reference.
        """
        response = super().finalize_response(request, response, *args, **kwargs)
        # Adding this header should be moved to global middleware, not just this endpoint
        return expose_header('Date', response)


class SequenceMetadata(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Request details for a sequence/subsection

    **Example Requests**

        GET /api/courseware/sequence/{usage_key}

    **Response Values**

        Body consists of the following fields:
            TODO

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course/usage_key is not available or cannot be seen.
        * 422 if the usage key is valid but does not have sequence metadata (like a unit or a problem)
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )

    def get(self, request, usage_key_string, *args, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """
        Return response to a GET request.
        """
        try:
            usage_key = UsageKey.from_string(usage_key_string)
        except InvalidKeyError as exc:
            raise NotFound(f"Invalid usage key: '{usage_key_string}'.") from exc
        _, request.user = setup_masquerade(
            request,
            usage_key.course_key,
            staff_access=has_access(request.user, 'staff', usage_key.course_key),
            reset_masquerade_data=True,
        )

        sequence, _ = get_module_by_usage_id(
            self.request,
            str(usage_key.course_key),
            str(usage_key),
            disable_staff_debug_info=True,
            will_recheck_access=True)

        if not hasattr(sequence, 'get_metadata'):
            # Looks like we were asked for metadata on something that is not a sequence (or section).
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        view = STUDENT_VIEW
        if request.user.is_anonymous:
            view = PUBLIC_VIEW

        context = {'specific_masquerade': is_masquerading_as_specific_student(request.user, usage_key.course_key)}
        return Response(sequence.get_metadata(view=view, context=context))


class Resume(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Request the last completed block in a course

    **Example Requests**

        GET /api/courseware/resume/{course_key}

    **Response Values**

        Body consists of the following fields:

            * block: the last completed block key
            * section: the key to the section
            * unit: the key to the unit
        If no completion data is available, the keys will be null

    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_key_string, *args, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """
        Return response to a GET request.
        """
        course_id = CourseKey.from_string(course_key_string)
        resp = {
            'block_id': None,
            'section_id': None,
            'unit_id': None,
        }

        try:
            block_key = get_key_to_last_completed_block(request.user, course_id)
            path = path_to_location(modulestore(), block_key, request, full_path=True)
            resp['section_id'] = str(path[2])
            resp['unit_id'] = str(path[3])
            resp['block_id'] = str(block_key)

        except (ItemNotFoundError, NoPathToItem, UnavailableCompletionData):
            pass  # leaving all the IDs as None indicates a redirect to the first unit in the course, as a backup

        return Response(resp)


class Celebration(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Marks a particular celebration as complete

    **Example Requests**

        POST /api/courseware/celebration/{course_key}

    **Request Parameters**

        Body consists of the following fields:

            * first_section (bool): whether we should celebrate when a user finishes their first section of a course
            * weekly_goal (bool): whether we should celebrate when a user hits their weekly learning goal in a course

    **Returns**

        * 200 or 201 or 202 on success with above fields.
        * 400 if an invalid parameter was sent.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)
    http_method_names = ['post']

    def post(self, request, course_key_string, *args, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """
        Handle a POST request.
        """
        course_key = CourseKey.from_string(course_key_string)

        # Check if we're masquerading as someone else. If so, we should just ignore this request.
        _, user = setup_masquerade(
            request,
            course_key,
            staff_access=has_access(request.user, 'staff', course_key),
            reset_masquerade_data=True,
        )
        if user != request.user:
            return Response(status=202)  # "Accepted"

        data = dict(request.data)
        first_section = data.pop('first_section', None)
        weekly_goal = data.pop('weekly_goal', None)
        if data:
            return Response(status=400)  # there were parameters we didn't recognize

        enrollment = CourseEnrollment.get_enrollment(request.user, course_key)
        if not enrollment:
            return Response(status=404)

        defaults = {}
        if first_section is not None:
            defaults['celebrate_first_section'] = first_section
        if weekly_goal is not None:
            defaults['celebrate_weekly_goal'] = weekly_goal

        if defaults:
            _, created = CourseEnrollmentCelebration.objects.update_or_create(enrollment=enrollment, defaults=defaults)
            return Response(status=201 if created else 200)
        else:
            return Response(status=200)  # just silently allow it
