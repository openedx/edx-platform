"""
Helpers for courseware app
"""
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseInstructorRole
from lms.djangoapps.courseware.courses import get_courses as get_courses_core
from openedx.adg.lms.applications.models import MultilingualCourseGroup
from openedx.adg.lms.utils.env_utils import is_testing_environment
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user


def get_courses(user):
    """
    Return courses using core method if environment is test environment else uses customized method for courses list.
    """
    return get_courses_core(user) if is_testing_environment() else MultilingualCourseGroup.objects.get_courses(user)


def get_course_instructors(course_key, request=None):
    """
    Gets all the instructor profiles and image_urls associated for the given course key

    Arguments:
        request: request object
        course_key: Course for which to fetch all the instructor data

    Returns:
        list: A list of tuples containing respectively, a list containing UserProfile objects for all
            the instructors, and a dict containing the profile image url in the {'size':'url'} format
    """
    course_locator = course_key.to_course_locator() if getattr(course_key, 'ccx', None) else course_key

    instructors = CourseInstructorRole(course_locator).users_with_role()
    instructor_data = []

    for instructor in instructors:
        profile_image_urls_for_instructor = get_profile_image_urls_for_user(instructor, request=request)
        instructor_data.append((instructor.profile, profile_image_urls_for_instructor,))

    return instructor_data


def get_extra_context(request, course):
    """
    Return all the extra context for the course_about page

    Arguments:
        request (Request): Request object
        course (CourseOverview): Course Overview object to add data to the context

    Returns:
        dict: Returns an empty dict if it is the testing environment otherwise returns a dict with added context
    """
    course_group = course.multilingual_course.multilingual_course_group
    course_languages = course_group.multilingual_courses.open_multilingual_courses().language(course.language)
    course_intructors = get_course_instructors(course.id, request=request)
    print(course_intructors)
    course_enrollment_count = CourseEnrollment.objects.enrollment_counts(course.id).get('total', 0)

    context = {
        "languages": course_languages,
        "instructors": course_intructors,
        "total_enrollments": course_enrollment_count,
        "self_paced": course.self_paced,
        "effort": course.effort
    }

    return {} if is_testing_environment() else context
