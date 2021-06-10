"""
Helpers for courseware app
"""
from django.utils.translation import get_language_info

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.util.milestones_helpers import get_pre_requisite_courses_not_completed
from lms.djangoapps.courseware.courses import get_courses as get_courses_core
from openedx.adg.lms.applications.helpers import is_user_qualified_for_bu_prereq_courses
from openedx.adg.lms.applications.models import MultilingualCourse, MultilingualCourseGroup
from openedx.adg.lms.utils.env_utils import is_testing_environment


def get_courses(user):
    """
    Return courses using core method if environment is test environment else uses customized method for courses list.
    """
    if is_testing_environment():
        return get_courses_core(user)

    return MultilingualCourseGroup.objects.get_user_program_prereq_courses_and_all_non_prereq_courses(user)


def get_business_line_prereq_courses(user):
    """
    Get business line courses for a user.

    Args:
        user (User): User for which courses will be retrieved

    Returns:
        list: List of business line courses for the user
    """
    if not is_user_qualified_for_bu_prereq_courses(user):
        return

    return MultilingualCourseGroup.objects.get_user_business_line_and_common_business_line_prereq_courses(user)


def get_language_names_from_codes(language_codes_with_course_id):
    """
    Converts the codes to language names and returns a list

    Arguments:
        language_codes_with_course_id (QuerySet): a QuerySet of tuples containing (course_id, language_code)

    Returns:
        list: A list of tuples containing (course_id, language_name)
    """
    language_names_with_course_id = []

    for course_id, language_code in language_codes_with_course_id:
        language_name = get_language_info(language_code).get('name')
        language_names_with_course_id.append((course_id, language_name))

    return language_names_with_course_id


def get_extra_course_about_context(request, course):
    """
    Get all the extra context for the course_about page

    Arguments:
        request (Request): Request object
        course (CourseOverview): Course Overview object to add data to the context

    Returns:
        dict: Returns an empty dict if it is the testing environment otherwise returns a dict with added context
    """
    if is_testing_environment():
        return {}

    course_language_names = []

    multilingual_course = MultilingualCourse.objects.all().multilingual_course_with_course_id(course.id)
    if multilingual_course:
        course_group_courses = multilingual_course.multilingual_course_group.multilingual_courses
        course_language_codes = course_group_courses.open_multilingual_courses().language_codes_with_course_ids()
        course_language_names = get_language_names_from_codes(course_language_codes)

    course_enrollment_count = CourseEnrollment.objects.enrollment_counts(course.id).get('total')

    course_requirements = None
    if request.user.is_authenticated:
        course_requirements = get_pre_requisite_courses_not_completed(
            request.user,
            [course.id]
        )

    context = {
        'course_languages': course_language_names,
        'course_requirements': course_requirements,
        'total_enrollments': course_enrollment_count,
        'self_paced': course.self_paced,
        'effort': course.effort,
    }

    return context
