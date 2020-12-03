"""
All tests for applications helpers functions
"""
from unittest.mock import Mock

import pytest

from openedx.adg.lms.applications.constants import LOGO_IMAGE_MAX_SIZE
from openedx.adg.lms.applications.helpers import validate_logo_size


def test_validate_file_size_with_valid_size():
    """
    Verify that file size up to LOGO_IMAGE_MAX_SIZE is allowed
    """
    mocked_file = Mock()
    mocked_file.size = LOGO_IMAGE_MAX_SIZE
    validate_logo_size(mocked_file)


def test_validate_file_size_with_invalid_size():
    """
    Verify that size greater than LOGO_IMAGE_MAX_SIZE is not allowed
    """
    mocked_file = Mock()
    mocked_file.size = LOGO_IMAGE_MAX_SIZE + 1
    with pytest.raises(Exception):
        validate_logo_size(mocked_file)
