"""
Tests for views.py file of courseware_override
"""
import mock
import pytest

from common.djangoapps.student.roles import CourseInstructorRole
from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.courseware_override.helpers import get_course_instructors, get_language_names_from_codes
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

DUMMY_IMAGE_URLS = {'small': 'small_dummy_url', 'medium': 'medium_dummy_url', 'large': 'large_dummy_url'}


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
    language_codes_with_course_ids = []
    expected_output = []

    for language_code, language_name in zip(language_codes, language_names):
        course = CourseOverviewFactory(language=language_code)
        language_codes_with_course_ids.append((course.id, language_code))
        expected_output.append((course.id, language_name))

    assert get_language_names_from_codes(language_codes_with_course_ids) == expected_output
