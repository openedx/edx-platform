"""
Instructor Dashboard Views
"""


import datetime
import logging
import uuid
from functools import reduce

import json
import pytz
import six
import urllib
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseServerError
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from edx_when.api import is_enabled_for_course
from mock import patch
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from six import text_type
from six.moves.urllib.parse import urljoin
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from lms.djangoapps.bulk_email.api import is_bulk_email_feature_enabled
from common.djangoapps.course_modes.models import CourseMode, CourseModesArchive
from common.djangoapps.edxmako.shortcuts import render_to_response
from lms.djangoapps.certificates import api as certs_api
from lms.djangoapps.certificates.models import (
    CertificateGenerationConfiguration,
    CertificateGenerationHistory,
    CertificateInvalidation,
    CertificateStatuses,
    CertificateWhitelist,
    GeneratedCertificate
)
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import get_course_by_id, get_studio_url
from lms.djangoapps.courseware.module_render import get_module_by_usage_id
from lms.djangoapps.discussion.django_comment_client.utils import available_division_schemes, has_forum_access
from lms.djangoapps.grades.api import is_writable_gradebook_enabled
from openedx.core.djangoapps.course_groups.cohorts import DEFAULT_COHORT_NAME, get_course_cohorts, is_course_cohorted
from openedx.core.djangoapps.django_comment_common.models import FORUM_ROLE_ADMINISTRATOR, CourseDiscussionSettings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.verified_track_content.models import VerifiedTrackCohortedCourse
from openedx.core.djangolib.markup import HTML, Text
from openedx.core.lib.url_utils import quote_slashes
from openedx.core.lib.xblock_utils import wrap_xblock
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import (
    CourseFinanceAdminRole, CourseInstructorRole,
    CourseSalesAdminRole, CourseStaffRole
)
from common.djangoapps.util.json_request import JsonResponse
from xmodule.html_module import HtmlBlock
from xmodule.modulestore.django import modulestore
from xmodule.tabs import CourseTab

from .tools import get_units_with_due_date, title_or_url
from .. import permissions
from ..toggles import data_download_v2_is_enabled

log = logging.getLogger(__name__)


class InstructorDashboardTab(CourseTab):
    """
    Defines the Instructor Dashboard view type that is shown as a course tab.
    """

    type = "instructor"
    title = ugettext_noop('Instructor')
    view_name = "instructor_dashboard"
    is_dynamic = True    # The "Instructor" tab is instead dynamically added when it is enabled

    @classmethod
    def is_enabled(cls, course, user=None):
        """
        Returns true if the specified user has staff access.
        """
        return bool(user and user.is_authenticated and user.has_perm(permissions.VIEW_DASHBOARD, course.id))


def show_analytics_dashboard_message(course_key):
    """
    Defines whether or not the analytics dashboard URL should be displayed.

    Arguments:
        course_key (CourseLocator): The course locator to display the analytics dashboard message on.
    """
    if hasattr(course_key, 'ccx'):
        ccx_analytics_enabled = settings.FEATURES.get('ENABLE_CCX_ANALYTICS_DASHBOARD_URL', False)
        return settings.ANALYTICS_DASHBOARD_URL and ccx_analytics_enabled

    return settings.ANALYTICS_DASHBOARD_URL


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard_2(request, course_id):
    """ Display the instructor dashboard for a course. """
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        log.error(u"Unable to find course with course key %s while loading the Instructor Dashboard.", course_id)
        return HttpResponseServerError()

    course = get_course_by_id(course_key, depth=0)

    access = {
        'admin': request.user.is_staff,
        'instructor': bool(has_access(request.user, 'instructor', course)),
        'finance_admin': CourseFinanceAdminRole(course_key).has_user(request.user),
        'sales_admin': CourseSalesAdminRole(course_key).has_user(request.user),
        'staff': bool(has_access(request.user, 'staff', course)),
        'forum_admin': has_forum_access(request.user, course_key, FORUM_ROLE_ADMINISTRATOR),
        'data_researcher': request.user.has_perm(permissions.CAN_RESEARCH, course_key),
    }

    if not request.user.has_perm(permissions.VIEW_DASHBOARD, course_key):
        raise Http404()

    is_white_label = CourseMode.is_white_label(course_key)

    reports_enabled = configuration_helpers.get_value('SHOW_ECOMMERCE_REPORTS', False)

    sections = []
    if access['staff']:
        sections.extend([
            _section_course_info(course, access),
            _section_membership(course, access),
            _section_cohort_management(course, access),
            _section_discussions_management(course, access),
            _section_student_admin(course, access),
        ])
    if access['data_researcher']:
        sections.append(_section_data_download(course, access))

    analytics_dashboard_message = None
    if show_analytics_dashboard_message(course_key) and (access['staff'] or access['instructor']):
        # Construct a URL to the external analytics dashboard
        analytics_dashboard_url = '{0}/courses/{1}'.format(settings.ANALYTICS_DASHBOARD_URL, six.text_type(course_key))
        link_start = HTML(u"<a href=\"{}\" rel=\"noopener\" target=\"_blank\">").format(analytics_dashboard_url)
        analytics_dashboard_message = _(
            u"To gain insights into student enrollment and participation {link_start}"
            u"visit {analytics_dashboard_name}, our new course analytics product{link_end}."
        )
        analytics_dashboard_message = Text(analytics_dashboard_message).format(
            link_start=link_start, link_end=HTML("</a>"), analytics_dashboard_name=settings.ANALYTICS_DASHBOARD_NAME)

        # Temporarily show the "Analytics" section until we have a better way of linking to Insights
        sections.append(_section_analytics(course, access))

    # Check if there is corresponding entry in the CourseMode Table related to the Instructor Dashboard course
    course_mode_has_price = False
    paid_modes = CourseMode.paid_modes_for_course(course_key)
    if len(paid_modes) == 1:
        course_mode_has_price = True
    elif len(paid_modes) > 1:
        log.error(
            u"Course %s has %s course modes with payment options. Course must only have "
            u"one paid course mode to enable eCommerce options.",
            six.text_type(course_key), len(paid_modes)
        )

    if access['instructor'] and is_enabled_for_course(course_key):
        sections.insert(3, _section_extensions(course))

    # Gate access to course email by feature flag & by course-specific authorization
    if is_bulk_email_feature_enabled(course_key) and (access['staff'] or access['instructor']):
        sections.append(_section_send_email(course, access))
    # Gate access to Special Exam tab depending if either timed exams or proctored exams
    # are enabled in the course

    user_has_access = any([
        request.user.is_staff,
        CourseStaffRole(course_key).has_user(request.user),
        CourseInstructorRole(course_key).has_user(request.user)
    ])
    course_has_special_exams = course.enable_proctored_exams or course.enable_timed_exams
    can_see_special_exams = course_has_special_exams and user_has_access and settings.FEATURES.get(
        'ENABLE_SPECIAL_EXAMS', False)

    if can_see_special_exams:
        sections.append(_section_special_exams(course, access))
    # Certificates panel
    # This is used to generate example certificates
    # and enable self-generated certificates for a course.
    # Note: This is hidden for all CCXs
    certs_enabled = CertificateGenerationConfiguration.current().enabled and not hasattr(course_key, 'ccx')
    if certs_enabled and access['admin']:
        sections.append(_section_certificates(course))

    openassessment_blocks = modulestore().get_items(
        course_key, qualifiers={'category': 'openassessment'}
    )
    # filter out orphaned openassessment blocks
    openassessment_blocks = [
        block for block in openassessment_blocks if block.parent is not None
    ]
    if len(openassessment_blocks) > 0 and access['staff']:
        sections.append(_section_open_response_assessment(request, course, openassessment_blocks, access))

    disable_buttons = not CourseEnrollment.objects.is_small_course(course_key)

    certificate_white_list = CertificateWhitelist.get_certificate_white_list(course_key)
    generate_certificate_exceptions_url = reverse(
        'generate_certificate_exceptions',
        kwargs={'course_id': six.text_type(course_key), 'generate_for': ''}
    )
    generate_bulk_certificate_exceptions_url = reverse(
        'generate_bulk_certificate_exceptions',
        kwargs={'course_id': six.text_type(course_key)}
    )
    certificate_exception_view_url = reverse(
        'certificate_exception_view',
        kwargs={'course_id': six.text_type(course_key)}
    )

    certificate_invalidation_view_url = reverse(
        'certificate_invalidation_view',
        kwargs={'course_id': six.text_type(course_key)}
    )

    certificate_invalidations = CertificateInvalidation.get_certificate_invalidations(course_key)

    context = {
        'course': course,
        'studio_url': get_studio_url(course, 'course'),
        'sections': sections,
        'disable_buttons': disable_buttons,
        'analytics_dashboard_message': analytics_dashboard_message,
        'certificate_white_list': certificate_white_list,
        'certificate_invalidations': certificate_invalidations,
        'generate_certificate_exceptions_url': generate_certificate_exceptions_url,
        'generate_bulk_certificate_exceptions_url': generate_bulk_certificate_exceptions_url,
        'certificate_exception_view_url': certificate_exception_view_url,
        'certificate_invalidation_view_url': certificate_invalidation_view_url,
        'xqa_server': settings.FEATURES.get('XQA_SERVER', "http://your_xqa_server.com"),
    }

    return render_to_response('instructor/instructor_dashboard_2/instructor_dashboard_2.html', context)


## Section functions starting with _section return a dictionary of section data.

## The dictionary must include at least {
##     'section_key': 'circus_expo'
##     'section_display_name': 'Circus Expo'
## }

## section_key will be used as a css attribute, javascript tie-in, and template import filename.
## section_display_name will be used to generate link titles in the nav bar.

def _section_special_exams(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = six.text_type(course.id)
    proctoring_provider = course.proctoring_provider
    escalation_email = None
    if proctoring_provider == 'proctortrack':
        escalation_email = course.proctoring_escalation_email
    from edx_proctoring.api import is_backend_dashboard_available

    section_data = {
        'section_key': 'special_exams',
        'section_display_name': _('Special Exams'),
        'access': access,
        'course_id': course_key,
        'escalation_email': escalation_email,
        'show_dashboard': is_backend_dashboard_available(course_key),
    }
    return section_data


def _section_certificates(course):
    """Section information for the certificates panel.

    The certificates panel allows global staff to generate
    example certificates and enable self-generated certificates
    for a course.

    Arguments:
        course (Course)

    Returns:
        dict

    """
    example_cert_status = None
    html_cert_enabled = certs_api.has_html_certificates_enabled(course)
    if html_cert_enabled:
        can_enable_for_course = True
    else:
        example_cert_status = certs_api.example_certificates_status(course.id)

        # Allow the user to enable self-generated certificates for students
        # *only* once a set of example certificates has been successfully generated.
        # If certificates have been misconfigured for the course (for example, if
        # the PDF template hasn't been uploaded yet), then we don't want
        # to turn on self-generated certificates for students!
        can_enable_for_course = (
            example_cert_status is not None and
            all(
                cert_status['status'] == 'success'
                for cert_status in example_cert_status
            )
        )
    instructor_generation_enabled = settings.FEATURES.get('CERTIFICATES_INSTRUCTOR_GENERATION', False)
    certificate_statuses_with_count = {
        certificate['status']: certificate['count']
        for certificate in GeneratedCertificate.get_unique_statuses(course_key=course.id)
    }

    return {
        'section_key': 'certificates',
        'section_display_name': _('Certificates'),
        'example_certificate_status': example_cert_status,
        'can_enable_for_course': can_enable_for_course,
        'enabled_for_course': certs_api.cert_generation_enabled(course.id),
        'is_self_paced': course.self_paced,
        'instructor_generation_enabled': instructor_generation_enabled,
        'html_cert_enabled': html_cert_enabled,
        'active_certificate': certs_api.get_active_web_certificate(course),
        'certificate_statuses_with_count': certificate_statuses_with_count,
        'status': CertificateStatuses,
        'certificate_generation_history':
            CertificateGenerationHistory.objects.filter(course_id=course.id).order_by("-created"),
        'urls': {
            'generate_example_certificates': reverse(
                'generate_example_certificates',
                kwargs={'course_id': course.id}
            ),
            'enable_certificate_generation': reverse(
                'enable_certificate_generation',
                kwargs={'course_id': course.id}
            ),
            'start_certificate_generation': reverse(
                'start_certificate_generation',
                kwargs={'course_id': course.id}
            ),
            'start_certificate_regeneration': reverse(
                'start_certificate_regeneration',
                kwargs={'course_id': course.id}
            ),
            'list_instructor_tasks_url': reverse(
                'list_instructor_tasks',
                kwargs={'course_id': course.id}
            ),
        }
    }


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_POST
@login_required
def set_course_mode_price(request, course_id):
    """
    set the new course price and add new entry in the CourseModesArchive Table
    """
    try:
        course_price = int(request.POST['course_price'])
    except ValueError:
        return JsonResponse(
            {'message': _("Please Enter the numeric value for the course price")},
            status=400)  # status code 400: Bad Request

    currency = request.POST['currency']
    course_key = CourseKey.from_string(course_id)

    course_honor_mode = CourseMode.objects.filter(mode_slug='honor', course_id=course_key)
    if not course_honor_mode:
        return JsonResponse(
            {'message': _(u"CourseMode with the mode slug({mode_slug}) DoesNotExist").format(mode_slug='honor')},
            status=400)  # status code 400: Bad Request

    CourseModesArchive.objects.create(
        course_id=course_id, mode_slug='honor', mode_display_name='Honor Code Certificate',
        min_price=course_honor_mode[0].min_price, currency=course_honor_mode[0].currency,
        expiration_datetime=datetime.datetime.now(pytz.utc), expiration_date=datetime.date.today()
    )
    course_honor_mode.update(
        min_price=course_price,
        currency=currency
    )
    return JsonResponse({'message': _("CourseMode price updated successfully")})


def _section_course_info(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id

    section_data = {
        'section_key': 'course_info',
        'section_display_name': _('Course Info'),
        'access': access,
        'course_id': course_key,
        'course_display_name': course.display_name_with_default,
        'course_org': course.display_org_with_default,
        'course_number': course.display_number_with_default,
        'has_started': course.has_started(),
        'has_ended': course.has_ended(),
        'start_date': course.start,
        'end_date': course.end,
        'num_sections': len(course.children),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': six.text_type(course_key)}),
    }

    if settings.FEATURES.get('DISPLAY_ANALYTICS_ENROLLMENTS'):
        section_data['enrollment_count'] = CourseEnrollment.objects.enrollment_counts(course_key)

    if show_analytics_dashboard_message(course_key):
        #  dashboard_link is already made safe in _get_dashboard_link
        dashboard_link = _get_dashboard_link(course_key)
        #  so we can use Text() here so it's not double-escaped and rendering HTML on the front-end
        message = Text(
            _(u"Enrollment data is now available in {dashboard_link}.")
        ).format(dashboard_link=dashboard_link)
        section_data['enrollment_message'] = message

    if settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'):
        section_data['detailed_gitlogs_url'] = reverse(
            'gitlogs_detail',
            kwargs={'course_id': six.text_type(course_key)}
        )

    try:
        sorted_cutoffs = sorted(list(course.grade_cutoffs.items()), key=lambda i: i[1], reverse=True)
        advance = lambda memo, letter_score_tuple: u"{}: {}, ".format(letter_score_tuple[0], letter_score_tuple[1]) \
                                                   + memo
        section_data['grade_cutoffs'] = reduce(advance, sorted_cutoffs, "")[:-2]
    except Exception:  # pylint: disable=broad-except
        section_data['grade_cutoffs'] = "Not Available"

    try:
        section_data['course_errors'] = [(escape(a), '') for (a, _unused) in modulestore().get_course_errors(course.id)]
    except Exception:  # pylint: disable=broad-except
        section_data['course_errors'] = [('Error fetching errors', '')]

    return section_data


def _section_membership(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    ccx_enabled = settings.FEATURES.get('CUSTOM_COURSES_EDX', False) and course.enable_ccx
    enrollment_role_choices = configuration_helpers.get_value('MANUAL_ENROLLMENT_ROLE_CHOICES',
                                                              settings.MANUAL_ENROLLMENT_ROLE_CHOICES)

    section_data = {
        'section_key': 'membership',
        'section_display_name': _('Membership'),
        'access': access,
        'ccx_is_enabled': ccx_enabled,
        'enroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': six.text_type(course_key)}),
        'unenroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': six.text_type(course_key)}),
        'upload_student_csv_button_url': reverse(
            'register_and_enroll_students',
            kwargs={'course_id': six.text_type(course_key)}
        ),
        'modify_beta_testers_button_url': reverse(
            'bulk_beta_modify_access',
            kwargs={'course_id': six.text_type(course_key)}
        ),
        'list_course_role_members_url': reverse(
            'list_course_role_members',
            kwargs={'course_id': six.text_type(course_key)}
        ),
        'modify_access_url': reverse('modify_access', kwargs={'course_id': six.text_type(course_key)}),
        'list_forum_members_url': reverse('list_forum_members', kwargs={'course_id': six.text_type(course_key)}),
        'update_forum_role_membership_url': reverse(
            'update_forum_role_membership',
            kwargs={'course_id': six.text_type(course_key)}
        ),
        'enrollment_role_choices': enrollment_role_choices,
        'is_reason_field_enabled': configuration_helpers.get_value('ENABLE_MANUAL_ENROLLMENT_REASON_FIELD', False)
    }
    return section_data


def _section_cohort_management(course, access):
    """ Provide data for the corresponding cohort management section """
    course_key = course.id
    ccx_enabled = hasattr(course_key, 'ccx')
    section_data = {
        'section_key': 'cohort_management',
        'section_display_name': _('Cohorts'),
        'access': access,
        'ccx_is_enabled': ccx_enabled,
        'course_cohort_settings_url': reverse(
            'course_cohort_settings',
            kwargs={'course_key_string': six.text_type(course_key)}
        ),
        'cohorts_url': reverse('cohorts', kwargs={'course_key_string': six.text_type(course_key)}),
        'upload_cohorts_csv_url': reverse('add_users_to_cohorts', kwargs={'course_id': six.text_type(course_key)}),
        'verified_track_cohorting_url': reverse(
            'verified_track_cohorting', kwargs={'course_key_string': six.text_type(course_key)}
        ),
    }
    return section_data


def _section_discussions_management(course, access):
    """ Provide data for the corresponding discussion management section """
    course_key = course.id
    enrollment_track_schemes = available_division_schemes(course_key)
    section_data = {
        'section_key': 'discussions_management',
        'section_display_name': _('Discussions'),
        'is_hidden': (not is_course_cohorted(course_key) and
                      CourseDiscussionSettings.ENROLLMENT_TRACK not in enrollment_track_schemes),
        'discussion_topics_url': reverse('discussion_topics', kwargs={'course_key_string': six.text_type(course_key)}),
        'course_discussion_settings': reverse(
            'course_discussions_settings',
            kwargs={'course_key_string': six.text_type(course_key)}
        ),
    }
    return section_data


def _section_student_admin(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    is_small_course = CourseEnrollment.objects.is_small_course(course_key)

    section_data = {
        'section_key': 'student_admin',
        'section_display_name': _('Student Admin'),
        'access': access,
        'is_small_course': is_small_course,
        'get_student_enrollment_status_url': reverse(
            'get_student_enrollment_status',
            kwargs={'course_id': six.text_type(course_key)}
        ),
        'get_student_progress_url_url': reverse(
            'get_student_progress_url',
            kwargs={'course_id': six.text_type(course_key)}
        ),
        'enrollment_url': reverse('students_update_enrollment', kwargs={'course_id': six.text_type(course_key)}),
        'reset_student_attempts_url': reverse(
            'reset_student_attempts',
            kwargs={'course_id': six.text_type(course_key)}
        ),
        'reset_student_attempts_for_entrance_exam_url': reverse(
            'reset_student_attempts_for_entrance_exam',
            kwargs={'course_id': six.text_type(course_key)},
        ),
        'rescore_problem_url': reverse('rescore_problem', kwargs={'course_id': six.text_type(course_key)}),
        'override_problem_score_url': reverse(
            'override_problem_score',
            kwargs={'course_id': six.text_type(course_key)}
        ),
        'rescore_entrance_exam_url': reverse('rescore_entrance_exam', kwargs={'course_id': six.text_type(course_key)}),
        'student_can_skip_entrance_exam_url': reverse(
            'mark_student_can_skip_entrance_exam',
            kwargs={'course_id': six.text_type(course_key)},
        ),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': six.text_type(course_key)}),
        'list_entrace_exam_instructor_tasks_url': reverse(
            'list_entrance_exam_instructor_tasks',
            kwargs={'course_id': six.text_type(course_key)}
        ),
        'spoc_gradebook_url': reverse('spoc_gradebook', kwargs={'course_id': six.text_type(course_key)}),
    }
    if is_writable_gradebook_enabled(course_key) and settings.WRITABLE_GRADEBOOK_URL:
        section_data['writable_gradebook_url'] = '{}/{}'.format(settings.WRITABLE_GRADEBOOK_URL, text_type(course_key))
    return section_data


def _section_extensions(course):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'extensions',
        'section_display_name': _('Extensions'),
        'units_with_due_dates': [(title_or_url(unit), six.text_type(unit.location))
                                 for unit in get_units_with_due_date(course)],
        'change_due_date_url': reverse('change_due_date', kwargs={'course_id': six.text_type(course.id)}),
        'reset_due_date_url': reverse('reset_due_date', kwargs={'course_id': six.text_type(course.id)}),
        'show_unit_extensions_url': reverse('show_unit_extensions', kwargs={'course_id': six.text_type(course.id)}),
        'show_student_extensions_url': reverse(
            'show_student_extensions',
            kwargs={'course_id': six.text_type(course.id)}
        ),
    }
    return section_data


def _section_data_download(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id

    show_proctored_report_button = (
        settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False) and
        course.enable_proctored_exams
    )
    section_key = 'data_download_2' if data_download_v2_is_enabled(course_key) else 'data_download'
    section_data = {
        'section_key': section_key,
        'section_display_name': _('Data Download'),
        'access': access,
        'show_generate_proctored_exam_report_button': show_proctored_report_button,
        'get_problem_responses_url': reverse('get_problem_responses', kwargs={'course_id': six.text_type(course_key)}),
        'get_grading_config_url': reverse('get_grading_config', kwargs={'course_id': six.text_type(course_key)}),
        'get_students_features_url': reverse('get_students_features', kwargs={'course_id': six.text_type(course_key)}),
        'get_issued_certificates_url': reverse(
            'get_issued_certificates', kwargs={'course_id': six.text_type(course_key)}
        ),
        'get_students_who_may_enroll_url': reverse(
            'get_students_who_may_enroll', kwargs={'course_id': six.text_type(course_key)}
        ),
        'get_anon_ids_url': reverse('get_anon_ids', kwargs={'course_id': six.text_type(course_key)}),
        'list_proctored_results_url': reverse(
            'get_proctored_exam_results', kwargs={'course_id': six.text_type(course_key)}
        ),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': six.text_type(course_key)}),
        'list_report_downloads_url': reverse('list_report_downloads', kwargs={'course_id': six.text_type(course_key)}),
        'calculate_grades_csv_url': reverse('calculate_grades_csv', kwargs={'course_id': six.text_type(course_key)}),
        'problem_grade_report_url': reverse('problem_grade_report', kwargs={'course_id': six.text_type(course_key)}),
        'course_has_survey': True if course.course_survey_name else False,
        'course_survey_results_url': reverse(
            'get_course_survey_results', kwargs={'course_id': six.text_type(course_key)}
        ),
        'export_ora2_data_url': reverse('export_ora2_data', kwargs={'course_id': six.text_type(course_key)}),
        'export_ora2_submission_files_url': reverse(
            'export_ora2_submission_files', kwargs={'course_id': six.text_type(course_key)}
        ),
    }
    ######### EOL #############
    try:
        from xblockcompletion import views
        section_data['has_xblockcompletion'] = True
        section_data['xblockcompletion_url_resumen'] = '{}?{}'.format(reverse('xblockcompletion-data:data'), urllib.parse.urlencode({'format': 'resumen', 'course': six.text_type(course_key)}))
        section_data['xblockcompletion_url_all'] = '{}?{}'.format(reverse('xblockcompletion-data:data'), urllib.parse.urlencode({'format': 'all', 'course': six.text_type(course_key)}))
    except ImportError:
        section_data['has_xblockcompletion'] = False
    
    try:
        from gradeucursos import views
        section_data['has_gradeucursos'] = True
        section_data['gradeucursos_url_data'] = reverse('gradeucursos-export:data')
        section_data['gradeucursos_course'] = six.text_type(course_key)
        section_data['gradeucursos_grade_cutoff'] = views.Content().get_grade_cutoff(course_key)
        section_data['gradeucursos_assig_types'] = views.Content()._get_assignment_types(course_key)
    except ImportError:
        section_data['has_gradeucursos'] = False
    
    try:
        from eolreportcertificate import views
        section_data['has_eolreportcertificate'] = True
        section_data['eolreportcertificate_url'] = '{}?{}'.format(reverse('eolreportcertificate-export:data'), urllib.parse.urlencode({'course': six.text_type(course_key)}))
    except ImportError:
        section_data['has_eolreportcertificate'] = False
    ######### EOL #############
    if not access.get('data_researcher'):
        section_data['is_hidden'] = True
    return section_data


def null_applicable_aside_types(block):  # pylint: disable=unused-argument
    """
    get_aside method for monkey-patching into applicable_aside_types
    while rendering an HtmlBlock for email text editing. This returns
    an empty list.
    """
    return []


def _section_send_email(course, access):
    """ Provide data for the corresponding bulk email section """
    course_key = course.id

    # Monkey-patch applicable_aside_types to return no asides for the duration of this render
    with patch.object(course.runtime, 'applicable_aside_types', null_applicable_aside_types):
        # This HtmlBlock is only being used to generate a nice text editor.
        html_module = HtmlBlock(
            course.system,
            DictFieldData({'data': ''}),
            ScopeIds(None, None, None, course_key.make_usage_key('html', 'fake'))
        )
        fragment = course.system.render(html_module, 'studio_view')
    fragment = wrap_xblock(
        'LmsRuntime', html_module, 'studio_view', fragment, None,
        extra_data={"course-id": six.text_type(course_key)},
        usage_id_serializer=lambda usage_id: quote_slashes(six.text_type(usage_id)),
        # Generate a new request_token here at random, because this module isn't connected to any other
        # xblock rendering.
        request_token=uuid.uuid1().hex
    )
    cohorts = []
    if is_course_cohorted(course_key):
        cohorts = get_course_cohorts(course)
    course_modes = []
    if not VerifiedTrackCohortedCourse.is_verified_track_cohort_enabled(course_key):
        course_modes = CourseMode.modes_for_course(course_key, include_expired=True, only_selectable=False)
    email_editor = fragment.content
    section_data = {
        'section_key': 'send_email',
        'section_display_name': _('Email'),
        'access': access,
        'send_email': reverse('send_email', kwargs={'course_id': six.text_type(course_key)}),
        'editor': email_editor,
        'cohorts': cohorts,
        'course_modes': course_modes,
        'default_cohort_name': DEFAULT_COHORT_NAME,
        'list_instructor_tasks_url': reverse(
            'list_instructor_tasks', kwargs={'course_id': six.text_type(course_key)}
        ),
        'email_background_tasks_url': reverse(
            'list_background_email_tasks', kwargs={'course_id': six.text_type(course_key)}
        ),
        'email_content_history_url': reverse(
            'list_email_content', kwargs={'course_id': six.text_type(course_key)}
        ),
    }
    ## EOL
    try:
        from welcome_mail.models import WelcomeMail
        section_data['welcome_data'] = '{}'
        section_data['welcome-mail-save'] = reverse('welcome-mail:save', kwargs={'course_id': str(course_key)})
        if WelcomeMail.objects.filter(course_key=course_key).exists():
            mail = WelcomeMail.objects.get(course_key=course_key)
            section_data['welcome_data'] = json.dumps({'subject':mail.subject, 'message':mail.html_message, 'is_active':mail.is_active})
    except ImportError:
        log.error('WelcomeMail - App doesnt installed')
    ## END EOL
    return section_data


def _get_dashboard_link(course_key):
    """ Construct a URL to the external analytics dashboard """
    analytics_dashboard_url = u'{0}/courses/{1}'.format(settings.ANALYTICS_DASHBOARD_URL, six.text_type(course_key))
    link = HTML(u"<a href=\"{0}\" rel=\"noopener\" target=\"_blank\">{1}</a>").format(
        analytics_dashboard_url, settings.ANALYTICS_DASHBOARD_NAME
    )
    return link


def _section_analytics(course, access):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'instructor_analytics',
        'section_display_name': _('Analytics'),
        'access': access,
        'course_id': six.text_type(course.id),
    }
    return section_data


def _section_open_response_assessment(request, course, openassessment_blocks, access):
    """Provide data for the corresponding dashboard section """
    course_key = course.id

    ora_items = []
    parents = {}

    for block in openassessment_blocks:
        block_parent_id = six.text_type(block.parent)
        result_item_id = six.text_type(block.location)
        if block_parent_id not in parents:
            parents[block_parent_id] = modulestore().get_item(block.parent)
        assessment_name = _("Team") + " : " + block.display_name if block.teams_enabled else block.display_name
        ora_items.append({
            'id': result_item_id,
            'name': assessment_name,
            'parent_id': block_parent_id,
            'parent_name': parents[block_parent_id].display_name,
            'staff_assessment': 'staff-assessment' in block.assessment_steps,
            'url_base': reverse('xblock_view', args=[course.id, block.location, 'student_view']),
            'url_grade_available_responses': reverse('xblock_view', args=[course.id, block.location,
                                                                          'grade_available_responses_view']),
        })

    openassessment_block = openassessment_blocks[0]
    block, __ = get_module_by_usage_id(
        request, six.text_type(course_key), six.text_type(openassessment_block.location),
        disable_staff_debug_info=True, course=course
    )
    section_data = {
        'fragment': block.render('ora_blocks_listing_view', context={
            'ora_items': ora_items,
            'ora_item_view_enabled': settings.FEATURES.get('ENABLE_XBLOCK_VIEW_ENDPOINT', False)
        }),
        'section_key': 'open_response_assessment',
        'section_display_name': _('Open Responses'),
        'access': access,
        'course_id': six.text_type(course_key),
    }
    return section_data


def is_ecommerce_course(course_key):
    """
    Checks if the given course is an e-commerce course or not, by checking its SKU value from
    CourseMode records for the course
    """
    sku_count = len([mode.sku for mode in CourseMode.modes_for_course(course_key) if mode.sku])
    return sku_count > 0
