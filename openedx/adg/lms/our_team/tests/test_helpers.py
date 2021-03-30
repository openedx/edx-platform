"""
Tests for helper functions of our team app
"""
from unittest.mock import Mock

import pytest

from openedx.adg.lms.our_team.constants import PROFILE_IMAGE_MAX_SIZE
from openedx.adg.lms.our_team.helpers import validate_profile_image_size


def test_validate_profile_image_size_with_valid_size():
    """
    Verify that file size up to PROFILE_IMAGE_MAX_SIZE is allowed
    """
    mocked_file = Mock()
    mocked_file.size = PROFILE_IMAGE_MAX_SIZE
    validate_profile_image_size(mocked_file)


def test_validate_profile_image_size_with_invalid_size():
    """
    Verify that size greater than PROFILE_IMAGE_MAX_SIZE is not allowed
    """
    mocked_file = Mock()
    mocked_file.size = PROFILE_IMAGE_MAX_SIZE + 1
    with pytest.raises(Exception):
        validate_profile_image_size(mocked_file)
