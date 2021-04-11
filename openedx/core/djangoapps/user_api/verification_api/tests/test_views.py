""" Tests for API endpoints. """


import datetime
import json

import freezegun
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from lms.djangoapps.verify_student.models import ManualVerification, SoftwareSecurePhotoVerification, SSOVerification
from lms.djangoapps.verify_student.tests.factories import SSOVerificationFactory
from common.djangoapps.student.tests.factories import UserFactory

FROZEN_TIME = '2015-01-01'
VERIFY_STUDENT = {'DAYS_GOOD_FOR': 365}


class VerificationStatusViewTestsMixin:
    """ Base class for the tests on verification status views """
    VIEW_NAME = None
    CREATED_AT = datetime.datetime.strptime(FROZEN_TIME, '%Y-%m-%d')
    PASSWORD = 'test'

    def setUp(self):
        freezer = freezegun.freeze_time(FROZEN_TIME)
        freezer.start()
        self.addCleanup(freezer.stop)
        super().setUp()
        self.user = UserFactory(password=self.PASSWORD)
        self.staff = UserFactory(is_staff=True, password=self.PASSWORD)
        self.photo_verification = SoftwareSecurePhotoVerification.objects.create(user=self.user, status='submitted')
        self.path = reverse(self.VIEW_NAME, kwargs={'username': self.user.username})
        self.client.login(username=self.staff.username, password=self.PASSWORD)

    def assert_path_not_found(self, path):
        """ Assert the path returns HTTP 404. """
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def get_expected_response(self, *args, **kwargs):
        raise NotImplementedError

    def assert_verification_returned(self, verified=False):
        """ Assert the path returns HTTP 200 and returns appropriately-serialized data. """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        expected_expires = self.CREATED_AT + datetime.timedelta(settings.VERIFY_STUDENT['DAYS_GOOD_FOR'])

        expected = self.get_expected_response(verified=verified, expected_expires=expected_expires)
        self.assertEqual(json.loads(response.content.decode('utf-8')), expected)

    def test_authentication_required(self):
        """ The endpoint should return HTTP 403 if the user is not authenticated. """
        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 401)

    def test_no_verifications(self):
        """ The endpoint should return HTTP 404 if the user has no verifications. """
        user = UserFactory()
        path = reverse(self.VIEW_NAME, kwargs={'username': user.username})
        self.assert_path_not_found(path)

    def test_staff_user(self):
        """ The endpoint should be accessible to staff users. """
        self.client.logout()
        self.client.login(username=self.staff.username, password=self.PASSWORD)
        self.assert_verification_returned()

    def test_owner(self):
        """ The endpoint should be accessible to the user who submitted the verification request. """
        self.client.logout()
        self.client.login(username=self.user.username, password=self.PASSWORD)
        self.assert_verification_returned()

    def test_non_owner_nor_staff_user(self):
        """ The endpoint should NOT be accessible if the request is not made by the submitter or staff user. """
        user = UserFactory()
        self.client.login(username=user.username, password=self.PASSWORD)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 403)

    def test_non_existent_user(self):
        """ The endpoint should return HTTP 404 if the user does not exist. """
        path = reverse(self.VIEW_NAME, kwargs={'username': 'abc123'})
        self.assert_path_not_found(path)


@override_settings(VERIFY_STUDENT=VERIFY_STUDENT)
class PhotoVerificationStatusViewTests(VerificationStatusViewTestsMixin, TestCase):
    """ Tests for the PhotoVerificationStatusView endpoint. """
    VIEW_NAME = 'verification_status'

    def get_expected_response(self, *args, **kwargs):
        return {
            'status': self.photo_verification.status,
            'expiration_datetime': '{}Z'.format(kwargs.get('expected_expires').isoformat()),
            'is_verified': kwargs.get('verified')
        }

    def test_approved_verification(self):
        """ The endpoint should return that the user is verified if the user's verification is accepted. """
        self.photo_verification.status = 'approved'
        self.photo_verification.save()
        self.client.logout()
        self.client.login(username=self.user.username, password=self.PASSWORD)
        self.assert_verification_returned(verified=True)


@override_settings(VERIFY_STUDENT=VERIFY_STUDENT)
class VerificationsDetailsViewTests(VerificationStatusViewTestsMixin, TestCase):
    """ Tests for the IDVerificationDetails endpoint. """
    VIEW_NAME = 'verification_details'

    def get_expected_response(self, *args, **kwargs):
        return [{
            'type': 'Software Secure',
            'status': self.photo_verification.status,
            'expiration_datetime': '{}Z'.format(kwargs.get('expected_expires').isoformat()),
            'message': '',
            'updated_at': '{}Z'.format(self.CREATED_AT.isoformat())
        }]

    def test_multiple_verification_types(self):
        self.manual_verification = ManualVerification.objects.create(
            user=self.user,
            status='approved',
            reason='testing'
        )
        self.sso_verification = SSOVerificationFactory(user=self.user, status='approved')
        self.photo_verification.error_msg = 'tested_error'
        self.photo_verification.error_code = 'error_code'
        self.photo_verification.status = 'denied'
        self.photo_verification.save()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        expected_expires = self.CREATED_AT + datetime.timedelta(settings.VERIFY_STUDENT['DAYS_GOOD_FOR'])

        expected = [
            {
                'type': 'Software Secure',
                'status': self.photo_verification.status,
                'expiration_datetime': '{}Z'.format(expected_expires.isoformat()),
                'message': self.photo_verification.error_msg,
                'updated_at': '{}Z'.format(self.CREATED_AT.isoformat()),
            },
            {
                'type': 'SSO',
                'status': self.sso_verification.status,
                'expiration_datetime': '{}Z'.format(expected_expires.isoformat()),
                'message': '',
                'updated_at': '{}Z'.format(self.CREATED_AT.isoformat()),
            },
            {
                'type': 'Manual',
                'status': self.manual_verification.status,
                'expiration_datetime': '{}Z'.format(expected_expires.isoformat()),
                'message': self.manual_verification.reason,
                'updated_at': '{}Z'.format(self.CREATED_AT.isoformat()),
            },
        ]
        self.assertEqual(json.loads(response.content.decode('utf-8')), expected)

    def test_multiple_verification_instances(self):
        self.sso_verification = SSOVerificationFactory(user=self.user, status='approved')
        second_ss_photo_verification = SoftwareSecurePhotoVerification.objects.create(
            user=self.user,
            status='denied',
            error_msg='test error message for denial',
            error_code='plain_code'
        )
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        expected_expires = self.CREATED_AT + datetime.timedelta(settings.VERIFY_STUDENT['DAYS_GOOD_FOR'])

        expected = [
            {
                'type': 'Software Secure',
                'status': self.photo_verification.status,
                'expiration_datetime': '{}Z'.format(expected_expires.isoformat()),
                'message': self.photo_verification.error_msg,
                'updated_at': '{}Z'.format(self.CREATED_AT.isoformat()),
            },
            {
                'type': 'Software Secure',
                'status': second_ss_photo_verification.status,
                'expiration_datetime': '{}Z'.format(expected_expires.isoformat()),
                'message': second_ss_photo_verification.error_msg,
                'updated_at': '{}Z'.format(self.CREATED_AT.isoformat()),
            },
            {
                'type': 'SSO',
                'status': self.sso_verification.status,
                'expiration_datetime': '{}Z'.format(expected_expires.isoformat()),
                'message': '',
                'updated_at': '{}Z'.format(self.CREATED_AT.isoformat()),
            },
        ]
        self.assertEqual(json.loads(response.content.decode('utf-8')), expected)
