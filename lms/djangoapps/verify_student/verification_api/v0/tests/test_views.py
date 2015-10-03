""" Tests for API endpoints. """
from __future__ import unicode_literals
import datetime
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
import pytz

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from student.tests.factories import UserFactory


class PhotoVerificationStatusViewTests(TestCase):
    """ Tests for the PhotoVerificationStatusView endpoint. """
    CREATED_AT = datetime.datetime(year=2000, month=1, day=1, tzinfo=pytz.UTC)
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
    PASSWORD = 'test'

    def setUp(self):
        super(PhotoVerificationStatusViewTests, self).setUp()
        self.user = UserFactory.create()
        self.staff = UserFactory.create(is_staff=True)

        self.verification = SoftwareSecurePhotoVerification.objects.create(
            user=self.user,
            status='submitted'
        )
        self.verification.created_at = self.CREATED_AT
        self.verification.save()

        self.path = reverse('verification_api:v0:photo_verification_status', kwargs={'username': self.user.username})
        self.client.login(username=self.staff.username, password=self.PASSWORD)

    def assert_path_not_found(self, path):
        """ Assert the path returns HTTP 404. """
        response = self.client.get(path)
        self.assertEqual(response.status_code, 404)

    def assert_verification_returned(self):
        """ Assert the path returns HTTP 200 and returns appropriately-serialized data. """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)

        expires = self.CREATED_AT + datetime.timedelta(settings.VERIFY_STUDENT['DAYS_GOOD_FOR'])
        expected = {
            'username': self.verification.user.username,
            'status': 'submitted',
            'expires': expires.strftime(self.DATETIME_FORMAT) + 'Z'
        }
        self.assertEqual(json.loads(response.content), expected)

    def test_non_existent_user(self):
        """ The endpoint should return HTTP 404 if the user does not exist. """
        path = reverse('verification_api:v0:photo_verification_status', kwargs={'username': 'abc123'})
        self.assert_path_not_found(path)

    def test_no_verifications(self):
        """ The endpoint should return HTTP 404 if the user has no verifications. """
        user = UserFactory.create()
        path = reverse('verification_api:v0:photo_verification_status', kwargs={'username': user.username})
        self.assert_path_not_found(path)

    def test_authentication_required(self):
        """ The endpoint should return HTTP 403 if the user is not authenticated. """
        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 401)

    def test_staff_user(self):
        """ The endpoint should be accessible to staff users. """
        self.client.login(username=self.staff.username, password=self.PASSWORD)
        self.assert_verification_returned()

    def test_owner(self):
        """ The endpoint should be accessible to the user who submitted the verification request. """
        self.client.login(username=self.user.username, password=self.PASSWORD)
        self.assert_verification_returned()

    def test_non_owner_or_staff_user(self):
        """ The endpoint should NOT be accessible if the request is not made by the submitter or staff user. """
        user = UserFactory.create()
        self.client.login(username=user.username, password=self.PASSWORD)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 403)
