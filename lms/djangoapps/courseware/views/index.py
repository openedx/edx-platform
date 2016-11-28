"""
View for Courseware Index
"""
# pylint: disable=attribute-defined-outside-init
from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.timezone import UTC
from django.views.decorators.cache import cache_control
from django.views.generic import View
from django.shortcuts import redirect

from courseware.url_helpers import get_redirect_url_for_global_staff
from edxmako.shortcuts import render_to_response, render_to_string
import logging
import newrelic.agent
import urllib

from xblock.fragment import Fragment
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from shoppingcart.models import CourseRegistrationCode
from student.models import CourseEnrollment
from student.views import is_course_blocked
from student.roles import GlobalStaff
from util.views import ensure_valid_course_key
from xmodule.modulestore.django import modulestore
from xmodule.x_module import STUDENT_VIEW
from survey.utils import must_answer_survey

from ..access import has_access, _adjust_start_date_for_beta_testers
from ..access_utils import in_preview_mode
from ..courses import get_studio_url, get_course_with_access
from ..entrance_exams import (
    course_has_entrance_exam,
    get_entrance_exam_content,
    get_entrance_exam_score,
    user_has_passed_entrance_exam,
    user_must_complete_entrance_exam,
)
from ..exceptions import Redirect
from ..masquerade import setup_masquerade
from ..model_data import FieldDataCache
from ..module_render import toc_for_course, get_module_for_descriptor
from .views import get_current_child, registered_for_course


log = logging.getLogger("edx.courseware.views.index")
TEMPLATE_IMPORTS = {'urllib': urllib}
CONTENT_DEPTH = 2


class CoursewareIndex(View):
    """
    View class for the Courseware page.
    """
    @method_decorator(login_required)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id, chapter=None, section=None, position=None):
        """
        Displays courseware accordion and associated content.  If course, chapter,
        and section are all specified, renders the page, or returns an error if they
        are invalid.

        If section is not specified, displays the accordion opened to the right
        chapter.

        If neither chapter or section are specified, displays the user's most
        recent chapter, or the first chapter if this is the user's first visit.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
            chapter (unicode): chapter url_name
            section (unicode): section url_name
            position (unicode): position in module, eg of <sequential> module
        """
        self.course_key = CourseKey.from_string(course_id)
        self.request = request
        self.original_chapter_url_name = chapter
        self.original_section_url_name = section
        self.chapter_url_name = chapter
        self.section_url_name = section
        self.position = position
        self.chapter, self.section = None, None
        self.url = request.path

        try:
            self._init_new_relic()
            self._clean_position()
            with modulestore().bulk_operations(self.course_key):
                self.course = get_course_with_access(request.user, 'load', self.course_key, depth=CONTENT_DEPTH)
                self.is_staff = has_access(request.user, 'staff', self.course)
                self._setup_masquerade_for_effective_user()
                return self._get()
        except Redirect as redirect_error:
            return redirect(redirect_error.url)
        except UnicodeEncodeError:
            raise Http404("URL contains Unicode characters")
        except Http404:
            # let it propagate
            raise
        except Exception:  # pylint: disable=broad-except
            return self._handle_unexpected_error()

    def _setup_masquerade_for_effective_user(self):
        """
        Setup the masquerade information to allow the request to
        be processed for the requested effective user.
        """
        self.real_user = self.request.user
        self.masquerade, self.effective_user = setup_masquerade(
            self.request,
            self.course_key,
            self.is_staff,
            reset_masquerade_data=True
        )
        # Set the user in the request to the effective user.
        self.request.user = self.effective_user

    def _get(self):
        """
        Render the index page.
        """
        self._redirect_if_needed_to_access_course()
        self._prefetch_and_bind_course()

        if self.course.has_children_at_depth(CONTENT_DEPTH):
            self._reset_section_to_exam_if_required()
            self.chapter = self._find_chapter()
            self.section = self._find_section()

            if self.chapter and self.section:
                self._redirect_if_not_requested_section()
                self._save_positions()
                self._prefetch_and_bind_section()

        return render_to_response('courseware/courseware.html', self._create_courseware_context())

    def _redirect_if_not_requested_section(self):
        """
        If the resulting section and chapter are different from what was initially
        requested, redirect back to the index page, but with an updated URL that includes
        the correct section and chapter values.  We do this so that our analytics events
        and error logs have the appropriate URLs.
        """
        if (
                self.chapter.url_name != self.original_chapter_url_name or
                (self.original_section_url_name and self.section.url_name != self.original_section_url_name)
        ):
            raise Redirect(
                reverse(
                    'courseware_section',
                    kwargs={
                        'course_id': unicode(self.course_key),
                        'chapter': self.chapter.url_name,
                        'section': self.section.url_name,
                    },
                )
            )

    def _init_new_relic(self):
        """
        Initialize metrics for New Relic so we can slice data in New Relic Insights
        """
        newrelic.agent.add_custom_parameter('course_id', unicode(self.course_key))
        newrelic.agent.add_custom_parameter('org', unicode(self.course_key.org))

    def _clean_position(self):
        """
        Verify that the given position is an integer. If it is not positive, set it to 1.
        """
        if self.position is not None:
            try:
                self.position = max(int(self.position), 1)
            except ValueError:
                raise Http404(u"Position {} is not an integer!".format(self.position))

    def _redirect_if_needed_to_access_course(self):
        """
        Verifies that the user can enter the course.
        """
        self._redirect_if_needed_to_pay_for_course()
        self._redirect_if_needed_to_register()
        self._redirect_if_needed_for_prereqs()
        self._redirect_if_needed_for_course_survey()

    def _redirect_if_needed_to_pay_for_course(self):
        """
        Redirect to dashboard if the course is blocked due to non-payment.
        """
        self.real_user = User.objects.prefetch_related("groups").get(id=self.real_user.id)
        redeemed_registration_codes = CourseRegistrationCode.objects.filter(
            course_id=self.course_key,
            registrationcoderedemption__redeemed_by=self.real_user
        )
        if is_course_blocked(self.request, redeemed_registration_codes, self.course_key):
            # registration codes may be generated via Bulk Purchase Scenario
            # we have to check only for the invoice generated registration codes
            # that their invoice is valid or not
            log.warning(
                u'User %s cannot access the course %s because payment has not yet been received',
                self.real_user,
                unicode(self.course_key),
            )
            raise Redirect(reverse('dashboard'))

    def _redirect_if_needed_to_register(self):
        """
        Verify that the user is registered in the course.
        """
        if not registered_for_course(self.course, self.effective_user):
            log.debug(
                u'User %s tried to view course %s but is not enrolled',
                self.effective_user,
                unicode(self.course.id)
            )
            user_is_global_staff = GlobalStaff().has_user(self.effective_user)
            user_is_enrolled = CourseEnrollment.is_enrolled(self.effective_user, self.course_key)
            if user_is_global_staff and not user_is_enrolled:
                redirect_url = get_redirect_url_for_global_staff(self.course_key, _next=self.url)
                raise Redirect(redirect_url)
            raise Redirect(reverse('about_course', args=[unicode(self.course.id)]))

    def _redirect_if_needed_for_prereqs(self):
        """
        See if all pre-requisites (as per the milestones app feature) have been
        fulfilled. Note that if the pre-requisite feature flag has been turned off
        (default) then this check will always pass.
        """
        if not has_access(self.effective_user, 'view_courseware_with_prerequisites', self.course):
            # Prerequisites have not been fulfilled.
            # Therefore redirect to the Dashboard.
            log.info(
                u'User %d tried to view course %s '
                u'without fulfilling prerequisites',
                self.effective_user.id, unicode(self.course.id))
            raise Redirect(reverse('dashboard'))

    def _redirect_if_needed_for_course_survey(self):
        """
        Check to see if there is a required survey that must be taken before
        the user can access the course.
        """
        if must_answer_survey(self.course, self.effective_user):
            raise Redirect(reverse('course_survey', args=[unicode(self.course.id)]))

    def _reset_section_to_exam_if_required(self):
        """
        Check to see if an Entrance Exam is required for the user.
        """
        if (
                course_has_entrance_exam(self.course) and
                user_must_complete_entrance_exam(self.request, self.effective_user, self.course)
        ):
            exam_chapter = get_entrance_exam_content(self.effective_user, self.course)
            if exam_chapter and exam_chapter.get_children():
                exam_section = exam_chapter.get_children()[0]
                if exam_section:
                    self.chapter_url_name = exam_chapter.url_name
                    self.section_url_name = exam_section.url_name

    def _get_language_preference(self):
        """
        Returns the preferred language for the actual user making the request.
        """
        language_preference = get_user_preference(self.real_user, LANGUAGE_KEY)
        if not language_preference:
            language_preference = settings.LANGUAGE_CODE
        return language_preference

    def _is_masquerading_as_student(self):
        """
        Returns whether the current request is masquerading as a student.
        """
        return self.masquerade and self.masquerade.role == 'student'

    def _is_masquerading_as_specific_student(self):
        """
        Returns whether the current request is masqueurading as a specific student.
        """
        return self._is_masquerading_as_student() and self.masquerade.user_name

    def _find_block(self, parent, url_name, block_type, min_depth=None):
        """
        Finds the block in the parent with the specified url_name.
        If not found, calls get_current_child on the parent.
        """
        child = None
        if url_name:
            child = parent.get_child_by(lambda m: m.location.name == url_name)
            if not child:
                # User may be trying to access a child that isn't live yet
                if not self._is_masquerading_as_student():
                    raise Http404('No {block_type} found with name {url_name}'.format(
                        block_type=block_type,
                        url_name=url_name,
                    ))
            elif min_depth and not child.has_children_at_depth(min_depth - 1):
                child = None
        if not child:
            child = get_current_child(parent, min_depth=min_depth, requested_child=self.request.GET.get("child"))
        return child

    def _find_chapter(self):
        """
        Finds the requested chapter.
        """
        return self._find_block(self.course, self.chapter_url_name, 'chapter', CONTENT_DEPTH - 1)

    def _find_section(self):
        """
        Finds the requested section.
        """
        if self.chapter:
            return self._find_block(self.chapter, self.section_url_name, 'section')

    def _prefetch_and_bind_course(self):
        """
        Prefetches all descendant data for the requested section and
        sets up the runtime, which binds the request user to the section.
        """
        self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course_key, self.effective_user, self.course, depth=CONTENT_DEPTH,
        )

        self.course = get_module_for_descriptor(
            self.effective_user,
            self.request,
            self.course,
            self.field_data_cache,
            self.course_key,
            course=self.course,
        )

    def _prefetch_and_bind_section(self):
        """
        Prefetches all descendant data for the requested section and
        sets up the runtime, which binds the request user to the section.
        """
        # Pre-fetch all descendant data
        self.section = modulestore().get_item(self.section.location, depth=None)
        self.field_data_cache.add_descriptor_descendents(self.section, depth=None)

        # Bind section to user
        self.section = get_module_for_descriptor(
            self.effective_user,
            self.request,
            self.section,
            self.field_data_cache,
            self.course_key,
            self.position,
            course=self.course,
        )

    def _save_positions(self):
        """
        Save where we are in the course and chapter.
        """
        save_child_position(self.course, self.chapter_url_name)
        save_child_position(self.chapter, self.section_url_name)

    def _create_courseware_context(self):
        """
        Returns and creates the rendering context for the courseware.
        Also returns the table of contents for the courseware.
        """
        courseware_context = {
            'csrf': csrf(self.request)['csrf_token'],
            'COURSE_TITLE': self.course.display_name_with_default_escaped,
            'course': self.course,
            'init': '',
            'fragment': Fragment(),
            'staff_access': self.is_staff,
            'studio_url': get_studio_url(self.course, 'course'),
            'masquerade': self.masquerade,
            'real_user': self.real_user,
            'xqa_server': settings.FEATURES.get('XQA_SERVER', "http://your_xqa_server.com"),
            'bookmarks_api_url': reverse('bookmarks'),
            'language_preference': self._get_language_preference(),
            'disable_optimizely': True,
        }
        table_of_contents = toc_for_course(
            self.effective_user,
            self.request,
            self.course,
            self.chapter_url_name,
            self.section_url_name,
            self.field_data_cache,
        )
        courseware_context['accordion'] = render_accordion(
            self.request,
            self.course,
            table_of_contents['chapters'],
        )

        # entrance exam data
        if course_has_entrance_exam(self.course):
            if getattr(self.chapter, 'is_entrance_exam', False):
                courseware_context['entrance_exam_current_score'] = get_entrance_exam_score(self.request, self.course)
                courseware_context['entrance_exam_passed'] = user_has_passed_entrance_exam(self.request, self.course)

        # staff masquerading data
        now = datetime.now(UTC())
        effective_start = _adjust_start_date_for_beta_testers(self.effective_user, self.course, self.course_key)
        if not in_preview_mode() and self.is_staff and now < effective_start:
            # Disable student view button if user is staff and
            # course is not yet visible to students.
            courseware_context['disable_student_access'] = True

        if self.section:
            # chromeless data
            if self.section.chrome:
                chrome = [s.strip() for s in self.section.chrome.lower().split(",")]
                if 'accordion' not in chrome:
                    courseware_context['disable_accordion'] = True
                if 'tabs' not in chrome:
                    courseware_context['disable_tabs'] = True

            # default tab
            if self.section.default_tab:
                courseware_context['default_tab'] = self.section.default_tab

            # section data
            courseware_context['section_title'] = self.section.display_name_with_default_escaped
            section_context = self._create_section_context(
                table_of_contents['previous_of_active_section'],
                table_of_contents['next_of_active_section'],
            )
            courseware_context['fragment'] = self.section.render(STUDENT_VIEW, section_context)

        return courseware_context

    def _create_section_context(self, previous_of_active_section, next_of_active_section):
        """
        Returns and creates the rendering context for the section.
        """
        def _compute_section_url(section_info, requested_child):
            """
            Returns the section URL for the given section_info with the given child parameter.
            """
            return "{url}?child={requested_child}".format(
                url=reverse(
                    'courseware_section',
                    args=[unicode(self.course_key), section_info['chapter_url_name'], section_info['url_name']],
                ),
                requested_child=requested_child,
            )

        section_context = {
            'activate_block_id': self.request.GET.get('activate_block_id'),
            'requested_child': self.request.GET.get("child"),
            'progress_url': reverse('progress', kwargs={'course_id': unicode(self.course_key)}),
        }
        if previous_of_active_section:
            section_context['prev_url'] = _compute_section_url(previous_of_active_section, 'last')
        if next_of_active_section:
            section_context['next_url'] = _compute_section_url(next_of_active_section, 'first')
        # sections can hide data that masquerading staff should see when debugging issues with specific students
        section_context['specific_masquerade'] = self._is_masquerading_as_specific_student()
        return section_context

    def _handle_unexpected_error(self):
        """
        Handle unexpected exceptions raised by View.
        """
        # In production, don't want to let a 500 out for any reason
        if settings.DEBUG:
            raise
        log.exception(
            u"Error in index view: user=%s, effective_user=%s, course=%s, chapter=%s section=%s position=%s",
            self.real_user,
            self.effective_user,
            unicode(self.course_key),
            self.chapter_url_name,
            self.section_url_name,
            self.position,
        )
        try:
            return render_to_response('courseware/courseware-error.html', {
                'staff_access': self.is_staff,
                'course': self.course
            })
        except:
            # Let the exception propagate, relying on global config to
            # at least return a nice error message
            log.exception("Error while rendering courseware-error page")
            raise


def render_accordion(request, course, table_of_contents):
    """
    Returns the HTML that renders the navigation for the given course.
    Expects the table_of_contents to have data on each chapter and section,
    including which ones are active.
    """
    context = dict(
        [
            ('toc', table_of_contents),
            ('course_id', unicode(course.id)),
            ('csrf', csrf(request)['csrf_token']),
            ('due_date_display_format', course.due_date_display_format),
        ] + TEMPLATE_IMPORTS.items()
    )
    return render_to_string('courseware/accordion.html', context)


def save_child_position(seq_module, child_name):
    """
    child_name: url_name of the child
    """
    for position, child in enumerate(seq_module.get_display_items(), start=1):
        if child.location.name == child_name:
            # Only save if position changed
            if position != seq_module.position:
                seq_module.position = position
    # Save this new position to the underlying KeyValueStore
    seq_module.save()


def save_positions_recursively_up(user, request, field_data_cache, xmodule, course=None):
    """
    Recurses up the course tree starting from a leaf
    Saving the position property based on the previous node as it goes
    """
    current_module = xmodule

    while current_module:
        parent_location = modulestore().get_parent_location(current_module.location)
        parent = None
        if parent_location:
            parent_descriptor = modulestore().get_item(parent_location)
            parent = get_module_for_descriptor(
                user,
                request,
                parent_descriptor,
                field_data_cache,
                current_module.location.course_key,
                course=course
            )

        if parent and hasattr(parent, 'position'):
            save_child_position(parent, current_module.location.name)

        current_module = parent
