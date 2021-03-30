""" Tests for LMS helper """
import pytest

from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory
from openedx.adg.lms.helpers import get_user_first_name

from .constants import FIRST_NAME, FIRST_PART_OF_FULL_NAME


@pytest.mark.django_db
@pytest.mark.parametrize(
    'first_name, full_name, expected_first_name', [
        (FIRST_NAME, '', FIRST_NAME),
        ('', f'{FIRST_PART_OF_FULL_NAME} last_part_of_full_name', FIRST_PART_OF_FULL_NAME)
    ],
    ids=['user_with_first_name', 'user_with_full_name']
)
def test_get_user_first_name(first_name, full_name, expected_first_name):
    """
    Tests `get_user_first_name` helper
    """
    user = UserFactory(first_name=first_name)
    UserProfileFactory(user=user, name=full_name)

    assert get_user_first_name(user) == expected_first_name
