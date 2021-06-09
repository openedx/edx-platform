"""
Tests for helpers.py file of courseware_override
"""
import mock
import pytest

from common.djangoapps.student.roles import CourseInstructorRole
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from openedx.adg.lms.applications.tests.factories import MultilingualCourseFactory
from openedx.adg.lms.courseware_override.helpers import (
    get_course_instructors,
    get_extra_course_about_context,
    get_language_names_from_codes
)
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

from .constants import DUMMY_IMAGE_URLS, EFFORT


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


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.courseware_override.helpers.get_profile_image_urls_for_user')
@pytest.mark.parametrize('users', [0, 1, 2], indirect=True)
def test_get_course_instructors(profile_image_urls_mock, users):
    """
    Tests if all the data related to the course instructors i.e the profile and the image urls are fetched
    correctly or not
    """
    course = CourseOverviewFactory()
    expected_output = []

    profile_image_urls_mock.return_value = DUMMY_IMAGE_URLS

    for user in users:
        CourseInstructorRole(course.id).add_users(user)
        expected_output.append({'profile': user.profile, 'profile_image_urls': DUMMY_IMAGE_URLS})

    assert get_course_instructors(course.id) == expected_output


@pytest.mark.django_db
@pytest.mark.parametrize(
    'language_codes, language_names', [(['en'], ['English']), (['ar', 'en'], ['Arabic', 'English'])]
)
def test_get_language_name_from_codes(language_codes, language_names):
    """
    Tests if the correct language names are being returned, with their respective course_ids
    """
    language_codes_with_course_ids = []
    expected_output = []

    for language_code, language_name in zip(language_codes, language_names):
        course = CourseOverviewFactory(language=language_code)
        language_codes_with_course_ids.append((course.id, language_code))
        expected_output.append((course.id, language_name))

    assert get_language_names_from_codes(language_codes_with_course_ids) == expected_output


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.courseware_override.helpers.is_testing_environment')
@mock.patch('openedx.adg.lms.courseware_override.helpers.get_course_instructors')
@mock.patch('openedx.adg.lms.courseware_override.helpers.get_pre_requisite_courses_not_completed')
@mock.patch('openedx.adg.lms.courseware_override.helpers.get_language_names_from_codes')
def test_get_extra_course_about_context(
    mock_get_lang_names, mock_get_pre_requisite_courses_not_completed, mock_get_instructors, mock_testing_env, request
):
    """
    Test if the context is being returned correctly by the get_extra_course_about_context function
    """
    user = UserFactory()
    request.user = user
    course = CourseOverviewFactory(self_paced=True, effort=EFFORT, language='en')
    CourseInstructorRole(course.id).add_users(user)
    CourseEnrollmentFactory(user=user, course=course)
    MultilingualCourseFactory(course=course)

    course_languages_with_ids = [(course.id, 'English')]
    instructor_profiles_with_image_urls = [{"profile": user.profile, "profile_image_urls": DUMMY_IMAGE_URLS}]

    mock_get_lang_names.return_value = course_languages_with_ids
    mock_get_instructors.return_value = instructor_profiles_with_image_urls
    mock_get_pre_requisite_courses_not_completed.return_value = None
    mock_testing_env.return_value = False

    expected_context = {
        'course_languages': course_languages_with_ids,
        'course_requirements': None,
        'instructors': instructor_profiles_with_image_urls,
        'total_enrollments': 1,
        'self_paced': True,
        'effort': EFFORT,
    }

    assert get_extra_course_about_context(request, course) == expected_context
