"""
Instructor Dashboard Views
"""

import logging
import datetime
import uuid
import pytz

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from edxmako.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.http import Http404
from django.conf import settings
from util.json_request import JsonResponse

from lms.lib.xblock.runtime import quote_slashes
from xmodule_modifiers import wrap_xblock
from xmodule.html_module import HtmlDescriptor
from xmodule.modulestore.django import modulestore
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from courseware.access import has_access
from courseware.courses import get_course_by_id, get_studio_url
from django_comment_client.utils import has_forum_access
from django_comment_common.models import FORUM_ROLE_ADMINISTRATOR
from student.models import CourseEnrollment
from shoppingcart.models import Coupon, PaidCourseRegistration
from course_modes.models import CourseMode, CourseModesArchive
from student.roles import CourseFinanceAdminRole

from class_dashboard.dashboard_data import get_section_display_name, get_array_section_has_problem
from .tools import get_units_with_due_date, title_or_url, bulk_email_is_enabled_for_course
from opaque_keys.edx.locations import SlashSeparatedCourseKey


log = logging.getLogger(__name__)


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard_2(request, course_id):
    """ Display the instructor dashboard for a course. """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = get_course_by_id(course_key, depth=None)

    access = {
        'admin': request.user.is_staff,
        'instructor': has_access(request.user, 'instructor', course),
        'finance_admin': CourseFinanceAdminRole(course_key).has_user(request.user),
        'staff': has_access(request.user, 'staff', course),
        'forum_admin': has_forum_access(
            request.user, course_key, FORUM_ROLE_ADMINISTRATOR
        ),
    }

    if not access['staff']:
        raise Http404()

    sections = [
        _section_course_info(course, access),
        _section_membership(course, access),
        _section_student_admin(course, access),
        _section_data_download(course, access),
        _section_analytics(course, access),
    ]

    #check if there is corresponding entry in the CourseMode Table related to the Instructor Dashboard course
    course_honor_mode = CourseMode.mode_for_course(course_key, 'honor')
    course_mode_has_price = False
    if course_honor_mode and course_honor_mode.min_price > 0:
        course_mode_has_price = True

    if (settings.FEATURES.get('INDIVIDUAL_DUE_DATES') and access['instructor']):
        sections.insert(3, _section_extensions(course))

    # Gate access to course email by feature flag & by course-specific authorization
    if bulk_email_is_enabled_for_course(course_key):
        sections.append(_section_send_email(course, access))

    # Gate access to Metrics tab by featue flag and staff authorization
    if settings.FEATURES['CLASS_DASHBOARD'] and access['staff']:
        sections.append(_section_metrics(course, access))

     # Gate access to Ecommerce tab
    if course_mode_has_price:
        sections.append(_section_e_commerce(course, access))

    disable_buttons = not _is_small_course(course_key)

    analytics_dashboard_message = None
    if settings.ANALYTICS_DASHBOARD_URL:
        # Construct a URL to the external analytics dashboard
        analytics_dashboard_url = '{0}/courses/{1}'.format(settings.ANALYTICS_DASHBOARD_URL, unicode(course_key))
        link_start = "<a href=\"{}\" target=\"_blank\">".format(analytics_dashboard_url)
        analytics_dashboard_message = _("To gain insights into student enrollment and participation {link_start}visit {analytics_dashboard_name}, our new course analytics product{link_end}.")
        analytics_dashboard_message = analytics_dashboard_message.format(
            link_start=link_start, link_end="</a>", analytics_dashboard_name=settings.ANALYTICS_DASHBOARD_NAME)

    context = {
        'course': course,
        'old_dashboard_url': reverse('instructor_dashboard_legacy', kwargs={'course_id': course_key.to_deprecated_string()}),
        'studio_url': get_studio_url(course, 'course'),
        'sections': sections,
        'disable_buttons': disable_buttons,
        'analytics_dashboard_message': analytics_dashboard_message
    }

    return render_to_response('instructor/instructor_dashboard_2/instructor_dashboard_2.html', context)


## Section functions starting with _section return a dictionary of section data.

## The dictionary must include at least {
##     'section_key': 'circus_expo'
##     'section_display_name': 'Circus Expo'
## }

## section_key will be used as a css attribute, javascript tie-in, and template import filename.
## section_display_name will be used to generate link titles in the nav bar.


def _section_e_commerce(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    coupons = Coupon.objects.filter(course_id=course_key).order_by('-is_active')
    course_price = None
    total_amount = None
    course_honor_mode = CourseMode.mode_for_course(course_key, 'honor')
    if course_honor_mode and course_honor_mode.min_price > 0:
        course_price = course_honor_mode.min_price
    if access['finance_admin']:
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(course_key)

    section_data = {
        'section_key': 'e-commerce',
        'section_display_name': _('E-Commerce'),
        'access': access,
        'course_id': course_key.to_deprecated_string(),
        'currency_symbol': settings.PAID_COURSE_REGISTRATION_CURRENCY[1],
        'ajax_remove_coupon_url': reverse('remove_coupon', kwargs={'course_id': course_key.to_deprecated_string()}),
        'ajax_get_coupon_info': reverse('get_coupon_info', kwargs={'course_id': course_key.to_deprecated_string()}),
        'get_user_invoice_preference_url': reverse('get_user_invoice_preference', kwargs={'course_id': course_key.to_deprecated_string()}),
        'sale_validation_url': reverse('sale_validation', kwargs={'course_id': course_key.to_deprecated_string()}),
        'ajax_update_coupon': reverse('update_coupon', kwargs={'course_id': course_key.to_deprecated_string()}),
        'ajax_add_coupon': reverse('add_coupon', kwargs={'course_id': course_key.to_deprecated_string()}),
        'get_sale_records_url': reverse('get_sale_records', kwargs={'course_id': course_key.to_deprecated_string()}),
        'get_sale_order_records_url': reverse('get_sale_order_records', kwargs={'course_id': course_key.to_deprecated_string()}),
        'instructor_url': reverse('instructor_dashboard', kwargs={'course_id': course_key.to_deprecated_string()}),
        'get_registration_code_csv_url': reverse('get_registration_codes', kwargs={'course_id': course_key.to_deprecated_string()}),
        'generate_registration_code_csv_url': reverse('generate_registration_codes', kwargs={'course_id': course_key.to_deprecated_string()}),
        'active_registration_code_csv_url': reverse('active_registration_codes', kwargs={'course_id': course_key.to_deprecated_string()}),
        'spent_registration_code_csv_url': reverse('spent_registration_codes', kwargs={'course_id': course_key.to_deprecated_string()}),
        'set_course_mode_url': reverse('set_course_mode_price', kwargs={'course_id': course_key.to_deprecated_string()}),
        'download_coupon_codes_url': reverse('get_coupon_codes', kwargs={'course_id': course_key.to_deprecated_string()}),
        'coupons': coupons,
        'course_price': course_price,
        'total_amount': total_amount
    }
    return section_data


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
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    course_honor_mode = CourseMode.objects.filter(mode_slug='honor', course_id=course_key)
    if not course_honor_mode:
        return JsonResponse(
            {'message': _("CourseMode with the mode slug({mode_slug}) DoesNotExist").format(mode_slug='honor')},
            status=400)  # status code 400: Bad Request

    CourseModesArchive.objects.create(
        course_id=course_id, mode_slug='honor', mode_display_name='Honor Code Certificate',
        min_price=getattr(course_honor_mode[0], 'min_price'), currency=getattr(course_honor_mode[0], 'currency'),
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
        'course_display_name': course.display_name,
        'has_started': course.has_started(),
        'has_ended': course.has_ended(),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': course_key.to_deprecated_string()}),
    }

    if settings.FEATURES.get('DISPLAY_ANALYTICS_ENROLLMENTS'):
        section_data['enrollment_count'] = CourseEnrollment.enrollment_counts(course_key)

    if settings.ANALYTICS_DASHBOARD_URL:
        dashboard_link = _get_dashboard_link(course_key)
        message = _("Enrollment data is now available in {dashboard_link}.").format(dashboard_link=dashboard_link)
        section_data['enrollment_message'] = message

    try:
        advance = lambda memo, (letter, score): "{}: {}, ".format(letter, score) + memo
        section_data['grade_cutoffs'] = reduce(advance, course.grade_cutoffs.items(), "")[:-2]
    except Exception:  # pylint: disable=broad-except
        section_data['grade_cutoffs'] = "Not Available"
    # section_data['offline_grades'] = offline_grades_available(course_key)

    try:
        section_data['course_errors'] = [(escape(a), '') for (a, _unused) in modulestore().get_course_errors(course.id)]
    except Exception:  # pylint: disable=broad-except
        section_data['course_errors'] = [('Error fetching errors', '')]

    return section_data


def _section_membership(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    section_data = {
        'section_key': 'membership',
        'section_display_name': _('Membership'),
        'access': access,
        'enroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': course_key.to_deprecated_string()}),
        'unenroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': course_key.to_deprecated_string()}),
        'upload_student_csv_button_url': reverse('register_and_enroll_students', kwargs={'course_id': course_key.to_deprecated_string()}),
        'modify_beta_testers_button_url': reverse('bulk_beta_modify_access', kwargs={'course_id': course_key.to_deprecated_string()}),
        'list_course_role_members_url': reverse('list_course_role_members', kwargs={'course_id': course_key.to_deprecated_string()}),
        'modify_access_url': reverse('modify_access', kwargs={'course_id': course_key.to_deprecated_string()}),
        'list_forum_members_url': reverse('list_forum_members', kwargs={'course_id': course_key.to_deprecated_string()}),
        'update_forum_role_membership_url': reverse('update_forum_role_membership', kwargs={'course_id': course_key.to_deprecated_string()}),
        'cohorts_ajax_url': reverse('cohorts', kwargs={'course_key_string': course_key.to_deprecated_string()}),
        'advanced_settings_url': get_studio_url(course, 'settings/advanced'),
    }
    return section_data


def _is_small_course(course_key):
    """ Compares against MAX_ENROLLMENT_INSTR_BUTTONS to determine if course enrollment is considered small. """
    is_small_course = False
    enrollment_count = CourseEnrollment.num_enrolled_in(course_key)
    max_enrollment_for_buttons = settings.FEATURES.get("MAX_ENROLLMENT_INSTR_BUTTONS")
    if max_enrollment_for_buttons is not None:
        is_small_course = enrollment_count <= max_enrollment_for_buttons
    return is_small_course


def _section_student_admin(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    is_small_course = _is_small_course(course_key)

    section_data = {
        'section_key': 'student_admin',
        'section_display_name': _('Student Admin'),
        'access': access,
        'is_small_course': is_small_course,
        'get_student_progress_url_url': reverse('get_student_progress_url', kwargs={'course_id': course_key.to_deprecated_string()}),
        'enrollment_url': reverse('students_update_enrollment', kwargs={'course_id': course_key.to_deprecated_string()}),
        'reset_student_attempts_url': reverse('reset_student_attempts', kwargs={'course_id': course_key.to_deprecated_string()}),
        'rescore_problem_url': reverse('rescore_problem', kwargs={'course_id': course_key.to_deprecated_string()}),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': course_key.to_deprecated_string()}),
        'spoc_gradebook_url': reverse('spoc_gradebook', kwargs={'course_id': course_key.to_deprecated_string()}),
    }
    return section_data


def _section_extensions(course):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'extensions',
        'section_display_name': _('Extensions'),
        'units_with_due_dates': [(title_or_url(unit), unit.location.to_deprecated_string())
                                 for unit in get_units_with_due_date(course)],
        'change_due_date_url': reverse('change_due_date', kwargs={'course_id': course.id.to_deprecated_string()}),
        'reset_due_date_url': reverse('reset_due_date', kwargs={'course_id': course.id.to_deprecated_string()}),
        'show_unit_extensions_url': reverse('show_unit_extensions', kwargs={'course_id': course.id.to_deprecated_string()}),
        'show_student_extensions_url': reverse('show_student_extensions', kwargs={'course_id': course.id.to_deprecated_string()}),
    }
    return section_data


def _section_data_download(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    section_data = {
        'section_key': 'data_download',
        'section_display_name': _('Data Download'),
        'access': access,
        'get_grading_config_url': reverse('get_grading_config', kwargs={'course_id': course_key.to_deprecated_string()}),
        'get_students_features_url': reverse('get_students_features', kwargs={'course_id': course_key.to_deprecated_string()}),
        'get_anon_ids_url': reverse('get_anon_ids', kwargs={'course_id': course_key.to_deprecated_string()}),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': course_key.to_deprecated_string()}),
        'list_report_downloads_url': reverse('list_report_downloads', kwargs={'course_id': course_key.to_deprecated_string()}),
        'calculate_grades_csv_url': reverse('calculate_grades_csv', kwargs={'course_id': course_key.to_deprecated_string()}),
    }
    return section_data


def _section_send_email(course, access):
    """ Provide data for the corresponding bulk email section """
    course_key = course.id

    # This HtmlDescriptor is only being used to generate a nice text editor.
    html_module = HtmlDescriptor(
        course.system,
        DictFieldData({'data': ''}),
        ScopeIds(None, None, None, course_key.make_usage_key('html', 'fake'))
    )
    fragment = course.system.render(html_module, 'studio_view')
    fragment = wrap_xblock(
        'LmsRuntime', html_module, 'studio_view', fragment, None,
        extra_data={"course-id": course_key.to_deprecated_string()},
        usage_id_serializer=lambda usage_id: quote_slashes(usage_id.to_deprecated_string()),
        # Generate a new request_token here at random, because this module isn't connected to any other
        # xblock rendering.
        request_token=uuid.uuid1().get_hex()
    )
    email_editor = fragment.content
    section_data = {
        'section_key': 'send_email',
        'section_display_name': _('Email'),
        'access': access,
        'send_email': reverse('send_email', kwargs={'course_id': course_key.to_deprecated_string()}),
        'editor': email_editor,
        'list_instructor_tasks_url': reverse(
            'list_instructor_tasks', kwargs={'course_id': course_key.to_deprecated_string()}
        ),
        'email_background_tasks_url': reverse(
            'list_background_email_tasks', kwargs={'course_id': course_key.to_deprecated_string()}
        ),
        'email_content_history_url': reverse(
            'list_email_content', kwargs={'course_id': course_key.to_deprecated_string()}
        ),
    }
    return section_data


def _get_dashboard_link(course_key):
    """ Construct a URL to the external analytics dashboard """
    analytics_dashboard_url = '{0}/courses/{1}'.format(settings.ANALYTICS_DASHBOARD_URL, unicode(course_key))
    link = "<a href=\"{0}\" target=\"_blank\">{1}</a>".format(analytics_dashboard_url,
                                                              settings.ANALYTICS_DASHBOARD_NAME)
    return link


def _section_analytics(course, access):
    """ Provide data for the corresponding dashboard section """
    course_key = course.id
    section_data = {
        'section_key': 'instructor_analytics',
        'section_display_name': _('Analytics'),
        'access': access,
        'get_distribution_url': reverse('get_distribution', kwargs={'course_id': course_key.to_deprecated_string()}),
        'proxy_legacy_analytics_url': reverse('proxy_legacy_analytics', kwargs={'course_id': course_key.to_deprecated_string()}),
    }

    if settings.ANALYTICS_DASHBOARD_URL:
        dashboard_link = _get_dashboard_link(course_key)
        message = _("Demographic data is now available in {dashboard_link}.").format(dashboard_link=dashboard_link)
        section_data['demographic_message'] = message

    return section_data


def _section_metrics(course, access):
    """Provide data for the corresponding dashboard section """
    course_key = course.id
    section_data = {
        'section_key': 'metrics',
        'section_display_name': _('Metrics'),
        'access': access,
        'course_id': course_key.to_deprecated_string(),
        'sub_section_display_name': get_section_display_name(course_key),
        'section_has_problem': get_array_section_has_problem(course_key),
        'get_students_opened_subsection_url': reverse('get_students_opened_subsection'),
        'get_students_problem_grades_url': reverse('get_students_problem_grades'),
        'post_metrics_data_csv_url': reverse('post_metrics_data_csv'),
    }
    return section_data
