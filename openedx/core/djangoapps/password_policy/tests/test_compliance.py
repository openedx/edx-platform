"""
Test password policy utilities
"""

from datetime import datetime, timedelta

import pytz
from dateutil.parser import parse as parse_date
from django.test import TestCase, override_settings
from mock import patch

from openedx.core.djangoapps.password_policy.compliance import (NonCompliantPasswordException,
                                                                NonCompliantPasswordWarning,
                                                                _check_user_compliance,
                                                                _get_compliance_deadline_for_user,
                                                                enforce_compliance_on_login,
                                                                should_enforce_compliance_on_login)
from common.djangoapps.student.tests.factories import (CourseAccessRoleFactory,
                                                       UserFactory)
from common.djangoapps.util.password_policy_validators import ValidationError


date1 = parse_date('2018-01-01 00:00:00+00:00')
date2 = parse_date('2018-02-02 00:00:00+00:00')
date3 = parse_date('2018-03-03 00:00:00+00:00')


class TestCompliance(TestCase):
    """
    Tests compliance methods for password policy
    """

    @override_settings(PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG={'ENFORCE_COMPLIANCE_ON_LOGIN': True})
    def test_should_enforce_compliance_on_login(self):
        """
        Test that if the config is disabled or nonexistent nothing is returned
        """
        # Parameters don't matter for this method as it only tests the config
        self.assertTrue(should_enforce_compliance_on_login())

    def test_enforce_compliance_on_login(self):
        """
        Verify that compliance does not need to be enforced if:
            * Password is compliant
            * There is no compliance deadline

        Verify that compliance does need to be enforced if:
            * Deadline has passed and the password is not compliant

        Verify that a warning is thrown if:
            * Deadline is in the future
        """
        user = UserFactory()
        password = 'S0m3p@ssw0rd'  # Don't actually need a password or user as methods will be mocked

        # Test password is compliant
        with patch('openedx.core.djangoapps.password_policy.compliance._check_user_compliance') as \
                mock_check_user_compliance:
            mock_check_user_compliance.return_value = True
            self.assertIsNone(enforce_compliance_on_login(user, password))

        # Test no deadline is set
        with patch('openedx.core.djangoapps.password_policy.compliance._check_user_compliance') as \
                mock_check_user_compliance:
            mock_check_user_compliance.return_value = False
            with patch('openedx.core.djangoapps.password_policy.compliance._get_compliance_deadline_for_user') as \
                    mock_get_compliance_deadline_for_user:
                mock_get_compliance_deadline_for_user.return_value = None
                self.assertIsNone(enforce_compliance_on_login(user, password))

        # Test deadline is in the past
        with patch('openedx.core.djangoapps.password_policy.compliance._check_user_compliance') as \
                mock_check_user_compliance:
            mock_check_user_compliance.return_value = False
            with patch('openedx.core.djangoapps.password_policy.compliance._get_compliance_deadline_for_user') as \
                    mock_get_compliance_deadline_for_user:
                mock_get_compliance_deadline_for_user.return_value = datetime.now(pytz.UTC) - timedelta(1)
                self.assertRaises(NonCompliantPasswordException, enforce_compliance_on_login, user, password)

        # Test deadline is in the future
        with patch('openedx.core.djangoapps.password_policy.compliance._check_user_compliance') as \
                mock_check_user_compliance:
            mock_check_user_compliance.return_value = False
            with patch('openedx.core.djangoapps.password_policy.compliance._get_compliance_deadline_for_user') as \
                    mock_get_compliance_deadline_for_user:
                mock_get_compliance_deadline_for_user.return_value = datetime.now(pytz.UTC) + timedelta(1)
                self.assertRaises(NonCompliantPasswordWarning, enforce_compliance_on_login, user, password)

    def test_check_user_compliance(self):
        """
        Test that if the config is enabled:
            * Returns True if the user has a compliant password
            * Returns False if the user does not have a compliant password
        """

        # Test that a user that passes validate_password returns True
        with patch('openedx.core.djangoapps.password_policy.compliance.validate_password') as \
                mock_validate_password:
            user = UserFactory()
            # Mock validate_password to return True without checking the password
            mock_validate_password.return_value = True
            self.assertTrue(_check_user_compliance(user, None))  # Don't need a password here

        # Test that a user that does not pass validate_password returns False
        with patch('openedx.core.djangoapps.password_policy.compliance.validate_password') as \
                mock_validate_password:
            user = UserFactory()
            # Mock validate_password to throw a ValidationError without checking the password
            mock_validate_password.side_effect = ValidationError('Some validation error')
            self.assertFalse(_check_user_compliance(user, None))  # Don't need a password here

    @override_settings(PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG={
        'STAFF_USER_COMPLIANCE_DEADLINE': date1,
        'ELEVATED_PRIVILEGE_USER_COMPLIANCE_DEADLINE': date2,
        'GENERAL_USER_COMPLIANCE_DEADLINE': date3,
    })
    def test_get_compliance_deadline_for_user(self):
        """
        Test that the proper deadlines get returned for each user scenario
            * Staff deadline returns STAFF_USER_COMPLIANCE_DEADLINE
            * CourseAccessRole Users return ELEVATED_PRIVILEGE_USER_COMPLIANCE_DEADLINE
            * Everyone else gets GENERAL_USER_COMPLIANCE_DEADLINE
        """
        # Staff user returned the STAFF_USER_COMPLIANCE_DEADLINE
        user = UserFactory(is_staff=True)
        self.assertEqual(date1, _get_compliance_deadline_for_user(user))

        # User with CourseAccessRole returns the ELEVATED_PRIVILEGE_USER_COMPLIANCE_DEADLINE
        user = UserFactory()
        CourseAccessRoleFactory.create(user=user)
        self.assertEqual(date2, _get_compliance_deadline_for_user(user))

        user = UserFactory()
        self.assertEqual(date3, _get_compliance_deadline_for_user(user))

    def test_get_compliance_deadline_for_user_fallbacks(self):
        """
        Test that when some deadlines aren't specified, we cascade from general to specific.
        """
        staff = UserFactory(is_staff=True)
        privileged = UserFactory()
        CourseAccessRoleFactory.create(user=privileged)
        both = UserFactory(is_staff=True)
        CourseAccessRoleFactory.create(user=both)
        user = UserFactory()

        only_general = {
            'GENERAL_USER_COMPLIANCE_DEADLINE': date3
        }
        with self.settings(PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG=only_general):
            self.assertEqual(date3, _get_compliance_deadline_for_user(staff))
            self.assertEqual(date3, _get_compliance_deadline_for_user(privileged))
            self.assertEqual(date3, _get_compliance_deadline_for_user(both))

        no_staff = {
            'ELEVATED_PRIVILEGE_USER_COMPLIANCE_DEADLINE': date2,
            'GENERAL_USER_COMPLIANCE_DEADLINE': date3
        }
        with self.settings(PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG=no_staff):
            self.assertEqual(date2, _get_compliance_deadline_for_user(both))
            self.assertEqual(date2, _get_compliance_deadline_for_user(staff))

        no_privileged = {
            'STAFF_USER_COMPLIANCE_DEADLINE': date1,
            'GENERAL_USER_COMPLIANCE_DEADLINE': date3
        }
        with self.settings(PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG=no_privileged):
            self.assertEqual(date1, _get_compliance_deadline_for_user(both))
            self.assertEqual(date3, _get_compliance_deadline_for_user(privileged))

        only_privileged = {
            'ELEVATED_PRIVILEGE_USER_COMPLIANCE_DEADLINE': date2,
        }
        with self.settings(PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG=only_privileged):
            self.assertEqual(date2, _get_compliance_deadline_for_user(both))
            self.assertEqual(date2, _get_compliance_deadline_for_user(staff))
            self.assertIsNone(_get_compliance_deadline_for_user(user))

        early_elevated = {
            'STAFF_USER_COMPLIANCE_DEADLINE': date2,
            'ELEVATED_PRIVILEGE_USER_COMPLIANCE_DEADLINE': date1,
        }
        with self.settings(PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG=early_elevated):
            self.assertEqual(date1, _get_compliance_deadline_for_user(both))
            self.assertEqual(date2, _get_compliance_deadline_for_user(staff))
            self.assertEqual(date1, _get_compliance_deadline_for_user(privileged))
            self.assertIsNone(_get_compliance_deadline_for_user(user))

        early_general = {
            'STAFF_USER_COMPLIANCE_DEADLINE': date3,
            'ELEVATED_PRIVILEGE_USER_COMPLIANCE_DEADLINE': date2,
            'GENERAL_USER_COMPLIANCE_DEADLINE': date1,
        }
        with self.settings(PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG=early_general):
            self.assertEqual(date1, _get_compliance_deadline_for_user(both))
            self.assertEqual(date1, _get_compliance_deadline_for_user(staff))
            self.assertEqual(date1, _get_compliance_deadline_for_user(privileged))
            self.assertEqual(date1, _get_compliance_deadline_for_user(user))
