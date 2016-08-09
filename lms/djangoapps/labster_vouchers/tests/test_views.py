"""
Tests labster voucher views.
./manage.py lms test --verbosity=1 lms/djangoapps/labster_vouchers   --traceback --settings=labster_test
"""
import json

from ddt import ddt, data
import mock
import httpretty
from django.conf import settings
from django.core.urlresolvers import reverse
from rest_framework import status

from student.models import CourseEnrollment
from enrollment.errors import (
    CourseNotFoundError, CourseEnrollmentError, CourseEnrollmentExistsError
)
from labster_course_license.tests.factories import CourseLicenseFactory
from openedx.core.djangoapps.labster.tests.base import CCXCourseTestBase


@ddt
@httpretty.activate
class TestActivateVouchers(CCXCourseTestBase):
    """
    Tests for set_license method.
    """

    def setUp(self):
        super(TestActivateVouchers, self).setUp()
        self.url = reverse("activate_voucher")
        self.client.login(username=self.user.username, password="test")

    def test_not_activated(self):
        """
        Ensure displays an error message when the user is not activated.
        """
        self.user.is_active = False
        self.user.save()
        voucher = "A" * 10
        res = self.client.post(self.url, data={"code": voucher}, follow=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(
            res,
            'Voucher cannot be applied, because your account has not been activated yet.'
        )

    def test_invalid_voucher(self):
        """
        Ensure displays an error message when voucher code is invalid.
        """
        res = self.client.post(self.url, data={"code": "invalid_code"}, follow=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(res, 'Enter a valid voucher code.')

    def test_no_license_for_voucher(self):
        """
        Ensure displays an error message when voucher code is invalid.
        """
        voucher = "A" * 10
        httpretty.register_uri(
            httpretty.GET,
            settings.LABSTER_ENDPOINTS.get('voucher_license').format(voucher),
            status=status.HTTP_404_NOT_FOUND,
        )

        res = self.client.post(self.url, data={"code": voucher}, follow=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(res, 'Cannot find a voucher')

    def test_already_active_voucher(self):
        """
        Ensure displays an error message when voucher code has been already activated.
        """
        err_message = "Error message."
        voucher = "A" * 10
        httpretty.register_uri(
            httpretty.GET,
            settings.LABSTER_ENDPOINTS.get('voucher_license').format(voucher),
            status=status.HTTP_200_OK,
            body=json.dumps({"error": err_message})
        )

        res = self.client.post(self.url, data={"code": voucher}, follow=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(res, err_message)

    def test_api_error(self):
        """
        Ensure displays an error message when API is unavailable.
        """
        voucher = "A" * 10
        httpretty.register_uri(
            httpretty.GET,
            settings.LABSTER_ENDPOINTS.get('voucher_license').format(voucher),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        res = self.client.post(self.url, data={"code": voucher}, follow=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(res, 'There are some issues with applying your voucher')

    def test_no_course(self):
        """
        Ensure displays an error message when edX cannot find a course for the voucher.
        """
        voucher = "A" * 10
        httpretty.register_uri(
            httpretty.GET,
            settings.LABSTER_ENDPOINTS.get('voucher_license').format(voucher),
            status=status.HTTP_200_OK,
            body=json.dumps({"license": "TestLicense"})
        )

        res = self.client.post(self.url, data={"code": voucher}, follow=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(res, 'Cannot find a course for the voucher')

    @data(CourseNotFoundError, CourseEnrollmentError, CourseEnrollmentExistsError)
    @mock.patch("labster_vouchers.views.add_enrollment")
    def test_enrollment_error(self, error, mock_add_enrollment):
        """
        Ensure displays an error message when edX raises error during enrollment.
        """
        if error == CourseEnrollmentExistsError:
            mock_add_enrollment.side_effect = error('Error', {})
        else:
            mock_add_enrollment.side_effect = error('Error')

        course_lic = CourseLicenseFactory.create(course_id=self.ccx_key)

        voucher = "A" * 10
        httpretty.register_uri(
            httpretty.GET,
            settings.LABSTER_ENDPOINTS.get('voucher_license').format(voucher),
            status=status.HTTP_200_OK,
            body=json.dumps({"license": course_lic.license_code})
        )

        res = self.client.post(self.url, data={"code": voucher}, follow=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertContains(res, 'submission-error is-shown')
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, course_lic.course_id))

    def test_can_enroll(self):
        """
        Ensure the student can be enrolled.
        """
        course_lic = CourseLicenseFactory.create(course_id=self.ccx_key)

        voucher = "A" * 10
        httpretty.register_uri(
            httpretty.GET,
            settings.LABSTER_ENDPOINTS.get('voucher_license').format(voucher),
            status=status.HTTP_200_OK,
            body=json.dumps({"license": course_lic.license_code})
        )
        httpretty.register_uri(
            httpretty.POST,
            settings.LABSTER_ENDPOINTS.get('voucher_activate'),
        )

        res = self.client.post(self.url, data={"code": voucher}, follow=False)

        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_lic.course_id))
        self.assertEqual(res.status_code, status.HTTP_302_FOUND)

        last_request = httpretty.last_request()
        self.assertItemsEqual(last_request.parsed_body.keys(), ['context_id', 'voucher', 'email', 'user_id'])

