"""
Test cases for the pluggable access control system.
"""
import ddt
import pytest

from django.conf import settings
from django.test.utils import override_settings
from django.test import TestCase
from mock import patch, Mock

from lms.lib.access_control_backends import AccessControlBackends


@ddt.ddt
class AccessControlBackendsTests(TestCase):
    """
    Tests for the AccessControlBackends class.
    """

    def setUp(self):
        """
        Instantiate a new AccessControlBackends object.
        """
        self.acl_backends = AccessControlBackends()

    def test_sanity_check(self):
        """
        Check that the settings are empty by default as well as no default backends are found.
        """
        assert settings.ACCESS_CONTROL_BACKENDS == {}
        assert self.acl_backends.backends == {}

    @ddt.data(
        {
            'first_config': {
                'course.see_in_catalog': {
                    'NAME': 'lms.lib:see_in_catalog_backend',
                }
            },
            'second_config': {},
            'expected_count': 1,
        },
        {
            'first_config': {},
            'second_config': {
                'course.see_in_catalog': {
                    'NAME': 'lms.lib:see_in_catalog_backend',
                }
            },
            'expected_count': 0,
        }
    )
    @ddt.unpack
    @patch('lms.lib.see_in_catalog_backend', Mock(), create=True)
    def test_backends_cache(self, first_config, second_config, expected_count):
        """
        Check the `@lazy` attribute behaviour.

        Ensures that the first use backend property loads the configuration.
        The second use of the property should use the cached results instead of re-reading the configs.
        """
        with override_settings(ACCESS_CONTROL_BACKENDS=first_config):
            assert len(self.acl_backends.backends) == expected_count, 'Should read the correct configs'

        with override_settings(ACCESS_CONTROL_BACKENDS=second_config):
            assert len(self.acl_backends.backends) == expected_count, 'Should not read the configs but use the cache'

    @override_settings(ACCESS_CONTROL_BACKENDS={
        'course.see_in_catalog': {
            'NAME': 'lms.lib:see_in_catalog_backend',
            'OPTIONS': {
                'dummy_option': 500,
            },
        }
    })
    @patch('lms.lib.see_in_catalog_backend', create=True)
    def test_settings_with_options(self, mock_backend):
        """
        Test the happy scenario for a backend with options.
        """
        assert self.acl_backends.backends == {
            'course.see_in_catalog': {
                'FUNC': mock_backend,
                'OPTIONS': {
                    'dummy_option': 500,
                },
            }
        }

    @override_settings(ACCESS_CONTROL_BACKENDS={
        'course.see_in_catalog': {
            'NAME': 'lms.lib:see_in_catalog_backend',
        }
    })
    @patch('lms.lib.access_control_backends.log')
    def test_settings_with_missing_function(self, mock_log):
        """
        Check that the system fails explicitly on a missing function.
        """
        with pytest.raises(AttributeError):
            _ = self.acl_backends.backends
        mock_log.exception.assert_called_with(
            'Something went wrong in reading the ACCESS_CONTROL_BACKENDS settings for `course.see_in_catalog`.'
        )

    @override_settings(ACCESS_CONTROL_BACKENDS={
        'studio.create_course': {
            'NAME': 'lms.lib:see_in_catalog_backend',
        }
    })
    def test_settings_with_unknown_actions(self):
        """
        Ensure only supported actions can be used.

        SUPPORTED_ACTIONS can be extended whenever needed.
        """
        with pytest.raises(NotImplementedError) as e:
            _ = self.acl_backends.backends
        assert e.match('`AccessControlBackends` does not support the action `studio.create_course` yet')

    @override_settings(ACCESS_CONTROL_BACKENDS={
        'course.enroll': {
            'NAME': 'lms.lib:enroll_backend',
            'OPTIONS': {
                'dummy_option': 500,
            },
        }
    })
    @ddt.data(True, False)
    def test_query_existing_backend(self, return_value):
        """
        Test a correctly working backend.
        """
        with patch('lms.lib.enroll_backend', create=True, return_value=return_value) as mock_backend:
            assert not mock_backend.call_count
            course = Mock()
            user = Mock()
            has_access = self.acl_backends.query('course.enroll', user, course, True)
            assert has_access == return_value
            mock_backend.assert_called_once_with(
                user=user,
                resource=course,
                default_has_access=True,
                options={
                    'dummy_option': 500,
                },
            )

    @override_settings(ACCESS_CONTROL_BACKENDS={})
    @ddt.data(True, False)
    def test_query_missing_backend(self, default_has_access):
        """
        Ensure that the `default_has_access` is used when querying an action without a plugged-in backend.
        """
        course = Mock()
        user = Mock()
        assert default_has_access == self.acl_backends.query('course.enroll', user, course, default_has_access)

    @override_settings(ACCESS_CONTROL_BACKENDS={
        'course.load': {
            'NAME': 'lms.lib:load_backend',
        }
    })
    @patch('lms.lib.load_backend', Mock(side_effect=ArithmeticError('Dividing by zero!')), create=True)
    @patch('lms.lib.access_control_backends.log')
    def test_query_broken_backend(self, mock_log):
        """
        Ensure a broken backend fails explicitly.
        """
        course = Mock()
        user = Mock()
        with pytest.raises(ArithmeticError):
            self.acl_backends.query('course.load', user, course, True)
        mock_log.exception.assert_called_once_with(
            'Something went wrong in querying the access control backend for `course.load`.'
        )
