""" Tests for LMS helper """
from unittest.mock import Mock

import pytest

from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory
from openedx.adg.lms.constants import IMAGE_MAX_SIZE
from openedx.adg.lms.helpers import get_user_first_name, validate_image_size

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


def test_validate_image_size_with_valid_size():
    """
    Verify that file size up to IMAGE_MAX_SIZE is allowed
    """
    mocked_file = Mock()
    mocked_file.size = IMAGE_MAX_SIZE
    validate_image_size(mocked_file)


def test_validate_image_size_with_invalid_size():
    """
    Verify that size greater than IMAGE_MAX_SIZE is not allowed
    """
    mocked_file = Mock()
    mocked_file.size = IMAGE_MAX_SIZE + 1
    with pytest.raises(Exception):
        validate_image_size(mocked_file)
