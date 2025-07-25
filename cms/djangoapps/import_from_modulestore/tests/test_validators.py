"""
Tests for import_from_modulestore validators
"""

from typing import get_args

from django.test import TestCase
import pytest

from cms.djangoapps.import_from_modulestore.validators import (
    validate_composition_level,
)
from cms.djangoapps.import_from_modulestore.data import CompositionLevel


class TestValidateCompositionLevel(TestCase):
    """
    Test cases for validate_composition_level function.
    Case 1: Valid composition level
    Case 2: Invalid composition level
    """

    def test_valid_composition_level(self):
        for level in get_args(CompositionLevel):
            # Should not raise an exception for valid levels
            validate_composition_level(level)

    def test_invalid_composition_level(self):
        with pytest.raises(ValueError) as exc:
            validate_composition_level('invalid_composition_level')
        assert 'Invalid composition level: invalid_composition_level' in str(exc.value)
