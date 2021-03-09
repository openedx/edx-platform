"""
Tests for views.py file of courseware_override
"""
import mock
import pytest

from common.djangoapps.student.roles import CourseInstructorRole
from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.courseware_override.helpers import get_course_instructors

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


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.courseware_override.helpers.get_profile_image_urls_for_user')
@pytest.mark.parametrize('users', [0, 1, 2], indirect=True)
def test_get_course_instructors(profile_image_urls_mock, get_course, users):
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

    assert get_course_instructors(course.id) == expected_output
