
import ddt
from unittest.mock import patch
import pytest

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from student.tests.factories import UserFactory
from openedx.core.djangoapps.user_authn.views.register import _skip_activation_email
from openedx.core.djangoapps.appsembler.api.helpers import (
    as_course_key,
    normalize_bool_param,
)
from openedx.core.djangoapps.appsembler.api.tests.factories import COURSE_ID_STR_TEMPLATE


class CourseKeyHelperTest(TestCase):

    def setUp(self):
        self.course_key_string = COURSE_ID_STR_TEMPLATE.format(1)
        self.course_key = CourseKey.from_string(self.course_key_string)

    def test_from_valid_string(self):
        course_key = as_course_key(self.course_key_string)
        assert isinstance(course_key, CourseKey)
        assert course_key == self.course_key
        assert course_key is not self.course_key

    def test_from_invalid_string(self):
        with pytest.raises(InvalidKeyError):
            as_course_key('some invalid string')

    def test_from_course_key(self):
        course_key = as_course_key(self.course_key)
        assert isinstance(course_key, CourseKey)
        assert course_key == self.course_key
        assert course_key is self.course_key

    def test_from_course_locator(self):
        course_locator = CourseLocator.from_string(
            self.course_key_string)
        course_key = as_course_key(course_locator)
        assert isinstance(course_key, CourseKey)
        assert course_key == self.course_key
        assert course_key is course_locator

    def test_from_invalid_type(self):
        with pytest.raises(TypeError):
            as_course_key(dict(foo='bar'))


class TestAPISendActivationEmail(TestCase):
    """
    Tests for _skip_activation_email for Tahoe Registration API and the related helpers.
    """

    @patch.dict('django.conf.settings.FEATURES', {'SKIP_EMAIL_VALIDATION': False})
    def test_skip_for_api_callers_upon_request(self):
        """
        Email should not be sent if the API caller wants to skip it.
        """
        user = UserFactory.create()

        helper_path = 'openedx.core.djangoapps.user_authn.views.register.skip_registration_email_for_registration_api'
        with patch(helper_path, return_value=True):
            assert _skip_activation_email(user, {}, None, {}), 'API requested: email can be skipped by AMC admin'


@ddt.ddt
class TestNormalizeBoolParamsHelper(TestCase):
    """
    Tests for the `normalize_bool_param` helper.
    """

    @ddt.data(False, 'False', 'false')
    def test_normalize_bool_param_falsy(self, unnormalized):
        normalized = normalize_bool_param(unnormalized)
        assert not normalized, 'Should consider `{}` as falsy'.format(unnormalized)

    @ddt.data(True, 'True', 'true')
    def test_normalize_bool_param_truthy(self, unnormalized):
        normalized = normalize_bool_param(unnormalized)
        assert normalized, 'Should consider `{}` as truthy'.format(unnormalized)

    @ddt.data(1, '2', '', None)
    def test_normalize_bool_param_exception(self, unnormalized):
        """Should raise exception on unexpected values."""
        with self.assertRaises(ValidationError):
            normalize_bool_param(unnormalized)
