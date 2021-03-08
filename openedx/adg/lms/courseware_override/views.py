"""
Override courseware views file
"""
import pycountry

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseInstructorRole
from openedx.adg.lms.applications.models import MultilingualCourseGroup
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user


def get_course_enrollment_count(course_key):
    """
    Get all number of total enrollments in a course, given the course key.

    Arguments:
        course_key: The course key for which to fetch the enrollment count

    Returns:
        int: Number of total enrollments
    """
    enrollments = CourseEnrollment.objects.enrollment_counts(course_key)
    return enrollments['total']


def get_all_languages_for_course(course):
    """
    Get a list of all the languages a particular course exists in.

    Arguments:
        course (CourseOverview): A course object

    Returns:
        list: A list containing the language names as str
    """
    languages = []

    course_language = pycountry.languages.get(alpha_2=course.language).name
    languages.append(course_language)

    multilingual_course_group = MultilingualCourseGroup.objects.filter(
        multilingual_courses__course=course).first()

    if multilingual_course_group:
        for multilingual_course in multilingual_course_group.open_multilingual_courses:
            course_language_code = multilingual_course.course.language
            language_name = pycountry.languages.get(alpha_2=course_language_code).name
            if language_name not in languages:
                languages.append(language_name)

    return languages


def get_all_course_instructors(course_key, request=None):
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
