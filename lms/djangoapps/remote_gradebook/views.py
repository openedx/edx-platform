"""
HTTP request handler functions for the remote gradebook app
"""

import logging

from django.contrib.auth.models import User
from django.db import transaction
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from opaque_keys.edx.locator import CourseLocator
from opaque_keys.edx.keys import CourseKey

import remote_gradebook.tasks
from remote_gradebook.utils import (
    get_assignment_grade_datatable,
    get_remote_gradebook_datatable_resp,
)
from courseware.access import has_access
from courseware.courses import get_course_by_id
from util.json_request import JsonResponse
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from lms.djangoapps.grades.context import grading_context_for_course
from instructor_task.api_helper import AlreadyRunningError
from instructor.views.api import require_level

log = logging.getLogger(__name__)


def enroll_emails_in_course(emails, course_key):
    """
    Attempts to enroll all provided emails in a course. Emails without a corresponding
    user have a CourseEnrollmentAllowed object created for the course.
    """
    results = {}
    for email in emails:
        user = User.objects.filter(email=email).first()
        result = ''
        if not user:
            _, created = CourseEnrollmentAllowed.objects.get_or_create(
                email=email,
                course_id=course_key
            )
            if created:
                result = 'User does not exist - created course enrollment permission'
            else:
                result = 'User does not exist - enrollment is already allowed'
        elif not CourseEnrollment.is_enrolled(user, course_key):
            try:
                CourseEnrollment.enroll(user, course_key)
                result = 'Enrolled user in the course'
            except Exception as ex:  # pylint: disable=broad-except
                result = 'Failed to enroll - {}'.format(ex)
        else:
            result = 'User already enrolled'
        results[email] = result
    return results


def get_enrolled_non_staff_users(course):
    """
    Returns an iterable of non-staff enrolled users for a given course
    """
    return [
        user for user in CourseEnrollment.objects.users_enrolled_in(course.id)
        if not has_access(user, 'staff', course)
    ]


def unenroll_non_staff_users_in_course(course):
    """
    Unenrolls non-staff users in a course
    """
    results = {}
    for enrolled_user in get_enrolled_non_staff_users(course):
        has_staff_access = has_access(enrolled_user, 'staff', course)
        if not has_staff_access:
            CourseEnrollment.unenroll(enrolled_user, course.id)
            result = 'Unenrolled user from the course'
        else:
            result = 'No action taken (staff user)'
        results[enrolled_user.email] = result
    return results


def get_assignment_type_label(course, assignment_type):
    """
    Gets the label for an assignment based on its type and the grading policy of the course.
    Returns the short label if one exists, or returns the full assignment type as the label
    if (a) the grading policy doesn't cover this assignment type, or (b) the grading policy
    has a blank short label for this assignment type
    """
    try:
        matching_policy = next(
            grader for grader in course.grading_policy['GRADER']
            if grader['type'] == assignment_type
        )
        return matching_policy['short_label'] if 'short_label' in matching_policy else assignment_type
    except StopIteration:
        return assignment_type


def get_course_assignment_labels(course):
    """
    Gets a list labels for all assignments in a course based on the assignment type and the
    grading policy of the course.
    E.g.: ['Hw 01', 'Hw 02', 'Ex 01', 'Lab']
    """
    grading_context = grading_context_for_course(course)
    graded_item_labels = []
    for graded_item_type, graded_items in grading_context['all_graded_subsections_by_type'].iteritems():
        label = get_assignment_type_label(course, graded_item_type)
        if len(graded_items) == 1:
            graded_item_labels.append(label)
        elif len(graded_items) > 1:
            for i, __ in enumerate(graded_items, start=1):
                graded_item_labels.append(
                    u"{label} {index:02d}".format(label=label, index=i)
                )
    return graded_item_labels


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_non_staff_enrollments(__, course_id):
    """
    Returns user emails that are enrolled in a course and not staff
    """
    course_id = CourseLocator.from_string(course_id)
    course = get_course_by_id(course_id)
    enrolled_non_staff_users = list(get_enrolled_non_staff_users(course))
    return JsonResponse({
        'count': len(enrolled_non_staff_users),
        'users': [user.email for user in enrolled_non_staff_users[0:20]]
    })


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_remote_gradebook_sections(request, course_id):
    """
    Returns a datatable of students and whether or not there is a match for those students
    in the remote gradebook
    """
    course_id = CourseLocator.from_string(course_id)
    course = get_course_by_id(course_id)
    error_msg, datatable = get_remote_gradebook_datatable_resp(request.user, course, 'get-sections')
    return JsonResponse({
        'errors': error_msg,
        'data': [datarow[0] for datarow in datatable.get('data', [])]
    })


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def list_matching_remote_enrolled_students(request, course_id):
    """
    Returns a datatable of students and whether or not there is a match for those students
    in the remote gradebook
    """
    course_id = CourseLocator.from_string(course_id)
    course = get_course_by_id(course_id)
    error_msg, rg_datatable = get_remote_gradebook_datatable_resp(request.user, course, 'get-membership')
    datatable = {}
    if not error_msg:
        enrolled_students = CourseEnrollment.objects.users_enrolled_in(course.id)
        rg_student_emails = [x['email'] for x in rg_datatable['retdata']]
        has_match = lambda student: 'Yes' if student.email in rg_student_emails else 'No'
        datatable = dict(
            header=['Student  email', 'Match?'],
            data=[[student.email, has_match(student)] for student in enrolled_students],
            title=_('Enrolled Students Matching Remote Gradebook'),
        )
    return JsonResponse({
        'errors': error_msg,
        'datatable': datatable
    })


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def list_remote_students_in_section(request, course_id):
    """
    Returns a datatable of students in the remote gradebook that are enrolled in a specific section
    """
    section_name = request.POST.get('section_name', '')
    course_id = CourseLocator.from_string(course_id)
    course = get_course_by_id(course_id)
    error_msg, datatable = get_remote_gradebook_datatable_resp(
        request.user,
        course,
        'get-membership',
        section=section_name
    )
    datatable['title'] = _('Enrolled Students in Section in Remote Gradebook')
    return JsonResponse({
        'errors': error_msg,
        'datatable': datatable
    })


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def add_enrollments_using_remote_gradebook(request, course_id):
    """
    Fetches enrollees for a course in a remote gradebook and enrolls those emails in the course in edX
    """
    unenroll_current = request.POST.get('unenroll_current', '').lower() == 'true'
    section_name = request.POST.get('section_name', '')
    course_id = CourseLocator.from_string(course_id)
    course = get_course_by_id(course_id)
    error_msg, rg_datatable = get_remote_gradebook_datatable_resp(
        request.user, course, 'get-membership', section=section_name
    )
    datatable = {}
    if not error_msg:
        datarow = []
        rg_student_emails = [x['email'] for x in rg_datatable['retdata']]
        enrollment_results = enroll_emails_in_course(rg_student_emails, course_id)
        datarow.extend([[email, result] for email, result in enrollment_results.items()])

        if unenroll_current:
            unenrollment_results = unenroll_non_staff_users_in_course(course)
            datarow.extend([[email, result] for email, result in unenrollment_results.items()])

        datatable = dict(
            header=['Email', 'Result'],
            data=datarow,
            title=_('Overload Enrollments from Remote Gradebook'),
        )
    return JsonResponse({
        'errors': error_msg,
        'datatable': datatable
    })


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def get_assignment_names(__, course_id):
    """
    Returns a datatable of the assignments available for this course
    """
    course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(course_key)
    assignment_names = get_course_assignment_labels(course)
    return JsonResponse({
        'data': assignment_names
    })


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def list_remote_assignments(request, course_id):
    """
    Returns a datatable of the assignments available in the remote gradebook
    """
    course_id = CourseLocator.from_string(course_id)
    course = get_course_by_id(course_id)
    error_msg, datatable = get_remote_gradebook_datatable_resp(request.user, course, 'get-assignments')
    datatable['title'] = _('Remote Gradebook Assignments')
    return JsonResponse({
        'errors': error_msg,
        'datatable': datatable,
    })


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def display_assignment_grades(request, course_id):
    """
    Returns a datatable of students' grades for an assignment in a course that matches a given course id
    """
    course_id = CourseLocator.from_string(course_id)
    course = get_course_by_id(course_id)
    error_msg, datatable = get_assignment_grade_datatable(course, request.POST.get('assignment_name', ''))
    return JsonResponse({
        'errors': error_msg,
        'datatable': datatable
    })


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def export_assignment_grades_to_rg(request, course_id):
    """
    Exports students' grades for an assignment to the remote gradebook, then returns a
    datatable of those grades
    """
    assignment_name = request.GET.get('assignment_name', '')
    course_id = CourseLocator.from_string(course_id)
    try:
        remote_gradebook.tasks.run_rgb_grade_export(
            request,
            course_id,
            assignment_name,
            request.user.email
        )
        log.info(
            u'Posting grades to RGB for user %s and course %s',
            request.user.username,
            course_id
        )
        success_status = _("Posting grades to remote grade book")
        return JsonResponse({"status": success_status})
    except AlreadyRunningError:
        already_running_status = _("Posting grades to remote grade book."
                                   " To view the status of the report, see Pending Tasks below."
                                   " You will be able to download the report when it is complete.")
        return JsonResponse({"status": already_running_status})


@transaction.non_atomic_requests
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_level('staff')
def export_assignment_grades_csv(request, course_id):
    """
    Creates a CSV of students' grades for an assignment and returns that CSV as an HTTP response
    """
    course_key = CourseLocator.from_string(course_id)
    assignment_name = request.GET.get('assignment_name', '')
    try:
        remote_gradebook.tasks.run_assignment_grades_csv_export(request, course_key, assignment_name)
        log.info(
            u'Exporting grades to CSV for user %s and course %s',
            request.user.username,
            course_id
        )
        success_status = _("The grade report is being created."
                           " To view the status of the report, see Pending Tasks below.")
        return JsonResponse({"status": success_status})
    except AlreadyRunningError:
        already_running_status = _("The grade report is currently being created."
                                   " To view the status of the report, see Pending Tasks below."
                                   " You will be able to download the report when it is complete.")
        return JsonResponse({"status": already_running_status})
