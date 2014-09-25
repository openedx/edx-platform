"""
Instructor Dashboard Views
"""

from django.utils.translation import ugettext as _
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from edxmako.shortcuts import render_to_response
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.http import Http404
from django.conf import settings

from xmodule_modifiers import wrap_xblock
from xmodule.html_module import HtmlDescriptor
from xmodule.modulestore import XML_MODULESTORE_TYPE, Location
from xmodule.modulestore.django import modulestore
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from courseware.access import has_access
from courseware.courses import get_course_by_id, get_cms_course_link, get_course_with_access
from django_comment_client.utils import has_forum_access
from django_comment_common.models import FORUM_ROLE_ADMINISTRATOR
from instructor.offline_gradecalc import student_grades
from student.models import CourseEnrollment
from bulk_email.models import CourseAuthorization
from class_dashboard.dashboard_data import get_section_display_name, get_array_section_has_problem

from .tools import get_units_with_due_date, title_or_url, bulk_email_is_enabled_for_course


@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def instructor_dashboard_2(request, course_id):
    """ Display the instructor dashboard for a course. """

    course = get_course_by_id(course_id, depth=None)
    is_studio_course = (modulestore().get_modulestore_type(course_id) != XML_MODULESTORE_TYPE)

    access = {
        'admin': request.user.is_staff,
        'instructor': has_access(request.user, course, 'instructor'),
        'staff': has_access(request.user, course, 'staff'),
        'forum_admin': has_forum_access(
            request.user, course_id, FORUM_ROLE_ADMINISTRATOR
        ),
    }

    if not access['staff']:
        raise Http404()

    sections = [
        _section_course_info(course_id, access),
        _section_membership(course_id, access),
        _section_student_admin(course_id, access),
        _section_data_download(course_id, access),
        _section_analytics(course_id, access),
    ]

    if (settings.FEATURES.get('INDIVIDUAL_DUE_DATES') and access['instructor']):
        sections.insert(3, _section_extensions(course))

    # Gate access to course email by feature flag & by course-specific authorization
    if bulk_email_is_enabled_for_course(course_id):
        sections.append(_section_send_email(course_id, access, course))

    # Gate access to Metrics tab by featue flag and staff authorization
    if settings.FEATURES['CLASS_DASHBOARD'] and access['staff']:
        sections.append(_section_metrics(course_id, access))

    studio_url = None
    if is_studio_course:
        studio_url = get_cms_course_link(course)

    enrollment_count = sections[0]['enrollment_count']
    disable_buttons = False
    max_enrollment_for_buttons = settings.FEATURES.get("MAX_ENROLLMENT_INSTR_BUTTONS")
    if max_enrollment_for_buttons is not None:
        disable_buttons = enrollment_count > max_enrollment_for_buttons

    context = {
        'course': course,
        'old_dashboard_url': reverse('instructor_dashboard_legacy', kwargs={'course_id': course_id}),
        'studio_url': studio_url,
        'sections': sections,
        'disable_buttons': disable_buttons,
    }

    return render_to_response('instructor/instructor_dashboard_2/instructor_dashboard_2.html', context)


"""
Section functions starting with _section return a dictionary of section data.

The dictionary must include at least {
    'section_key': 'circus_expo'
    'section_display_name': 'Circus Expo'
}

section_key will be used as a css attribute, javascript tie-in, and template import filename.
section_display_name will be used to generate link titles in the nav bar.
"""  # pylint: disable=W0105


def _section_course_info(course_id, access):
    """ Provide data for the corresponding dashboard section """
    course = get_course_by_id(course_id, depth=None)

    course_id_dict = Location.parse_course_id(course_id)

    section_data = {
        'section_key': 'course_info',
        'section_display_name': _('Course Info'),
        'access': access,
        'course_id': course_id,
        'course_org': course_id_dict['org'],
        'course_num': course_id_dict['course'],
        'course_name': course_id_dict['name'],
        'course_display_name': course.display_name,
        'enrollment_count': CourseEnrollment.num_enrolled_in(course_id),
        'has_started': course.has_started(),
        'has_ended': course.has_ended(),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': course_id}),
    }

    try:
        advance = lambda memo, (letter, score): "{}: {}, ".format(letter, score) + memo
        section_data['grade_cutoffs'] = reduce(advance, course.grade_cutoffs.items(), "")[:-2]
    except Exception:
        section_data['grade_cutoffs'] = "Not Available"
    # section_data['offline_grades'] = offline_grades_available(course_id)

    try:
        section_data['course_errors'] = [(escape(a), '') for (a, _unused) in modulestore().get_item_errors(course.location)]
    except Exception:
        section_data['course_errors'] = [('Error fetching errors', '')]

    return section_data


def _section_membership(course_id, access):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'membership',
        'section_display_name': _('Membership'),
        'access': access,
        'enroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': course_id}),
        'unenroll_button_url': reverse('students_update_enrollment', kwargs={'course_id': course_id}),
        'modify_beta_testers_button_url': reverse('bulk_beta_modify_access', kwargs={'course_id': course_id}),
        'list_course_role_members_url': reverse('list_course_role_members', kwargs={'course_id': course_id}),
        'modify_access_url': reverse('modify_access', kwargs={'course_id': course_id}),
        'list_forum_members_url': reverse('list_forum_members', kwargs={'course_id': course_id}),
        'update_forum_role_membership_url': reverse('update_forum_role_membership', kwargs={'course_id': course_id}),
    }
    return section_data


def _section_student_admin(course_id, access):
    """ Provide data for the corresponding dashboard section """
    is_small_course = False
    enrollment_count = CourseEnrollment.num_enrolled_in(course_id)
    max_enrollment_for_buttons = settings.FEATURES.get("MAX_ENROLLMENT_INSTR_BUTTONS")
    if max_enrollment_for_buttons is not None:
        is_small_course = enrollment_count <= max_enrollment_for_buttons

    section_data = {
        'section_key': 'student_admin',
        'section_display_name': _('Student Admin'),
        'access': access,
        'is_small_course': is_small_course,
        'get_student_progress_url_url': reverse('get_student_progress_url', kwargs={'course_id': course_id}),
        'enrollment_url': reverse('students_update_enrollment', kwargs={'course_id': course_id}),
        'reset_student_attempts_url': reverse('reset_student_attempts', kwargs={'course_id': course_id}),
        'rescore_problem_url': reverse('rescore_problem', kwargs={'course_id': course_id}),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': course_id}),
        'spoc_gradebook_url': reverse('spoc_gradebook', kwargs={'course_id': course_id}),
    }
    return section_data


def _section_extensions(course):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'extensions',
        'section_display_name': _('Extensions'),
        'units_with_due_dates': [(title_or_url(unit), unit.location.url())
                                 for unit in get_units_with_due_date(course)],
        'change_due_date_url': reverse('change_due_date', kwargs={'course_id': course.id}),
        'reset_due_date_url': reverse('reset_due_date', kwargs={'course_id': course.id}),
        'show_unit_extensions_url': reverse('show_unit_extensions', kwargs={'course_id': course.id}),
        'show_student_extensions_url': reverse('show_student_extensions', kwargs={'course_id': course.id}),
        'fix_extensions_url': reverse('fix_extensions', kwargs={'course_id': course.id}),
    }
    return section_data


def _section_data_download(course_id, access):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'data_download',
        'section_display_name': _('Data Download'),
        'access': access,
        'get_grading_config_url': reverse('get_grading_config', kwargs={'course_id': course_id}),
        'get_students_features_url': reverse('get_students_features', kwargs={'course_id': course_id}),
        'get_anon_ids_url': reverse('get_anon_ids', kwargs={'course_id': course_id}),
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': course_id}),
        'list_report_downloads_url': reverse('list_report_downloads', kwargs={'course_id': course_id}),
        'calculate_grades_csv_url': reverse('calculate_grades_csv', kwargs={'course_id': course_id}),
    }
    return section_data


def _section_send_email(course_id, access, course):
    """ Provide data for the corresponding bulk email section """
    html_module = HtmlDescriptor(
        course.system,
        DictFieldData({'data': ''}),
        ScopeIds(None, None, None, 'i4x://dummy_org/dummy_course/html/dummy_name')
    )
    fragment = course.system.render(html_module, 'studio_view')
    fragment = wrap_xblock('LmsRuntime', html_module, 'studio_view', fragment, None, extra_data={"course-id": course_id})
    email_editor = fragment.content
    section_data = {
        'section_key': 'send_email',
        'section_display_name': _('Email'),
        'access': access,
        'send_email': reverse('send_email', kwargs={'course_id': course_id}),
        'editor': email_editor,
        'list_instructor_tasks_url': reverse('list_instructor_tasks', kwargs={'course_id': course_id}),
        'email_background_tasks_url': reverse('list_background_email_tasks', kwargs={'course_id': course_id}),
    }
    return section_data


def _section_analytics(course_id, access):
    """ Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'analytics',
        'section_display_name': _('Analytics'),
        'access': access,
        'get_distribution_url': reverse('get_distribution', kwargs={'course_id': course_id}),
        'proxy_legacy_analytics_url': reverse('proxy_legacy_analytics', kwargs={'course_id': course_id}),
    }
    return section_data


def _section_metrics(course_id, access):
    """Provide data for the corresponding dashboard section """
    section_data = {
        'section_key': 'metrics',
        'section_display_name': ('Metrics'),
        'access': access,
        'course_id': course_id,
        'sub_section_display_name': get_section_display_name(course_id),
        'section_has_problem': get_array_section_has_problem(course_id),
        'get_students_opened_subsection_url': reverse('get_students_opened_subsection'),
        'get_students_problem_grades_url': reverse('get_students_problem_grades'),
        'post_metrics_data_csv_url': reverse('post_metrics_data_csv'),
    }
    return section_data


#---- Gradebook (shown to small courses only) ----
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
def spoc_gradebook(request, course_id):
    """
    Show the gradebook for this course:
    - Only shown for courses with enrollment < settings.FEATURES.get("MAX_ENROLLMENT_INSTR_BUTTONS")
    - Only displayed to course staff
    """
    course = get_course_with_access(request.user, course_id, 'staff', depth=None)

    enrolled_students = User.objects.filter(
        courseenrollment__course_id=course_id,
        courseenrollment__is_active=1
    ).order_by('username').select_related("profile")

    # TODO (vshnayder): implement pagination to show to large courses
    max_num_students = settings.FEATURES.get("MAX_ENROLLMENT_INSTR_BUTTONS")
    enrolled_students = enrolled_students[:max_num_students]   # HACK!

    student_info = [
        {
            'username': student.username,
            'id': student.id,
            'email': student.email,
            'grade_summary': student_grades(student, request, course),
            'realname': student.profile.name,
        }
        for student in enrolled_students
    ]

    return render_to_response('courseware/gradebook.html', {
        'students': student_info,
        'course': course,
        'course_id': course_id,
        # Checked above
        'staff_access': True,
        'ordered_grades': sorted(course.grade_cutoffs.items(), key=lambda i: i[1], reverse=True),
    })
