"""
Tests for views.py file of courseware_override
"""
from datetime import datetime, timedelta

import mock
import pytest

from common.djangoapps.student.roles import CourseInstructorRole
from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.applications.tests.factories import MultilingualCourseFactory, MultilingualCourseGroupFactory
from openedx.adg.lms.courseware_override.views import (
    get_all_course_instructors,
    get_all_languages_for_course,
    get_course_enrollment_count
)
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

START_DATE = datetime.today() - timedelta(days=365)
END_DATE = datetime.today() + timedelta(days=365)
DUMMY_IMAGE_URLS = {'small': 'small_dummy_url', 'medium': 'large_dummy_url', 'large': 'large_dummy_url'}


@pytest.mark.django_db
@pytest.fixture(name='users')
def user_fixture(request):
    """
    Create test users

    Returns:
        list: A list of User objects as specified
    """
    users = UserFactory.create_batch(request.param)
    return users


@pytest.fixture(scope='function', name='get_course')
def course_fixture():
    """
    Creates a function to create a course with the given language

    Returns:
        func: A function that allows user to create a course with the specified language
    """
    course_list = []

    def create_user(language='en'):
        """
        Create a course with the given language

        Arguments:
            language: The language code

        Returns:
             CourseOverview: A course overview object with the provided language
        """
        course = CourseOverviewFactory()
        course.language = language
        course.start_date = START_DATE
        course.end_date = END_DATE
        course.save()
        course_list.append(course)
        return course

    return create_user


@pytest.fixture(name='multilingual_course_group')
def multilingual_course_group_fixture():
    """
    Create a multilingual course group

    Returns:
        MultilingualCourseGroup object
    """
    multilingual_course_group = MultilingualCourseGroupFactory()
    return multilingual_course_group


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.courseware_override.views.CourseEnrollment')
@pytest.mark.parametrize(
    'enrollment_count,expected_result', [({'total': 0}, 0), ({'total': 1}, 1), ({'total': 5}, 5), ])
def test_get_course_enrollment_count(course_enrollment_mock, get_course, enrollment_count, expected_result):
    """
    Test whether the get_course_enrollment_count function fetches the correct amount of enrollments in a given
    course
    """
    dummy_course = get_course()
    course_enrollment_mock.objects.enrollment_counts.return_value = enrollment_count

    assert get_course_enrollment_count(dummy_course.id) == expected_result


@pytest.mark.django_db
@pytest.mark.parametrize(
    'languages,expected_languages', [(['ar'], ['Arabic']), (['ar', 'en'], ['Arabic', 'English'])])
def test_get_all_languages_for_course(get_course, multilingual_course_group, languages, expected_languages):
    """
    Tests if the get_all_languages_for_course gets all languages of all the courses in a multilingual course group
    in which the given course belongs to
    """
    course_list = []

    for language in languages:
        course = get_course(language=language)
        course_list.append(course)
        MultilingualCourseFactory(course=course, multilingual_course_group=multilingual_course_group)

    assert get_all_languages_for_course(course_list[0]) == expected_languages


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.courseware_override.views.get_profile_image_urls_for_user')
@pytest.mark.parametrize('users', [0, 1, 2], indirect=True)
def test_get_all_course_instructors(profile_image_urls_mock, get_course, users):
    """
    Tests if all the data related to the course instructors i.e the profile and the image urls are fetched
    correctly or not
    """
    course = get_course()
    expected_output = []

    profile_image_urls_mock.return_value = DUMMY_IMAGE_URLS

    for user in users:
        CourseInstructorRole(course.id).add_users(user)
        expected_output.append((user.profile, DUMMY_IMAGE_URLS))

    assert get_all_course_instructors(course.id) == expected_output
