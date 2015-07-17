"""
Tests for student enrollment.
"""
import ddt
from django.core.cache import cache
from nose.tools import raises
import unittest
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from enrollment import api
from enrollment.errors import EnrollmentApiLoadError, EnrollmentNotFoundError, CourseModeNotFoundError
from enrollment.tests import fake_data_api


@ddt.ddt
@override_settings(ENROLLMENT_DATA_API="enrollment.tests.fake_data_api")
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollmentTest(TestCase):
    """
    Test student enrollment, especially with different course modes.
    """
    USERNAME = "Bob"
    COURSE_ID = "some/great/course"

    def setUp(self):
        super(EnrollmentTest, self).setUp()
        fake_data_api.reset()
        cache.clear()

    @ddt.data(
        # Default (no course modes in the database)
        # Expect automatically being enrolled as "honor".
        ([], 'honor'),

        # Audit / Verified / Honor
        # We should always go to the "choose your course" page.
        # We should also be enrolled as "honor" by default.
        (['honor', 'verified', 'audit'], 'honor'),

        # Check for professional ed happy path.
        (['professional'], 'professional'),
        (['no-id-professional'], 'no-id-professional')
    )
    @ddt.unpack
    def test_enroll(self, course_modes, mode):
        # Add a fake course enrollment information to the fake data API
        fake_data_api.add_course(self.COURSE_ID, course_modes=course_modes)
        # Enroll in the course and verify the URL we get sent to
        result = api.add_enrollment(self.USERNAME, self.COURSE_ID, mode=mode)
        self.assertIsNotNone(result)
        self.assertEquals(result['student'], self.USERNAME)
        self.assertEquals(result['course']['course_id'], self.COURSE_ID)
        self.assertEquals(result['mode'], mode)

        get_result = api.get_enrollment(self.USERNAME, self.COURSE_ID)
        self.assertEquals(result, get_result)

    @raises(CourseModeNotFoundError)
    def test_prof_ed_enroll(self):
        # Add a fake course enrollment information to the fake data API
        fake_data_api.add_course(self.COURSE_ID, course_modes=['professional'])
        # Enroll in the course and verify the URL we get sent to
        api.add_enrollment(self.USERNAME, self.COURSE_ID, mode='verified')

    @ddt.data(
        # Default (no course modes in the database)
        # Expect that users are automatically enrolled as "honor".
        ([], 'honor'),

        # Audit / Verified / Honor
        # We should always go to the "choose your course" page.
        # We should also be enrolled as "honor" by default.
        (['honor', 'verified', 'audit'], 'honor'),

        # Check for professional ed happy path.
        (['professional'], 'professional'),
        (['no-id-professional'], 'no-id-professional')
    )
    @ddt.unpack
    def test_unenroll(self, course_modes, mode):
        # Add a fake course enrollment information to the fake data API
        fake_data_api.add_course(self.COURSE_ID, course_modes=course_modes)
        # Enroll in the course and verify the URL we get sent to
        result = api.add_enrollment(self.USERNAME, self.COURSE_ID, mode=mode)
        self.assertIsNotNone(result)
        self.assertEquals(result['student'], self.USERNAME)
        self.assertEquals(result['course']['course_id'], self.COURSE_ID)
        self.assertEquals(result['mode'], mode)
        self.assertTrue(result['is_active'])

        result = api.update_enrollment(self.USERNAME, self.COURSE_ID, mode=mode, is_active=False)
        self.assertIsNotNone(result)
        self.assertEquals(result['student'], self.USERNAME)
        self.assertEquals(result['course']['course_id'], self.COURSE_ID)
        self.assertEquals(result['mode'], mode)
        self.assertFalse(result['is_active'])

    @raises(EnrollmentNotFoundError)
    def test_unenroll_not_enrolled_in_course(self):
        # Add a fake course enrollment information to the fake data API
        fake_data_api.add_course(self.COURSE_ID, course_modes=['honor'])
        api.update_enrollment(self.USERNAME, self.COURSE_ID, mode='honor', is_active=False)

    @ddt.data(
        # Simple test of honor and verified.
        ([
            {'course_id': 'the/first/course', 'course_modes': [], 'mode': 'honor'},
            {'course_id': 'the/second/course', 'course_modes': ['honor', 'verified'], 'mode': 'verified'}
        ]),

        # No enrollments
        ([]),

        # One Enrollment
        ([
            {'course_id': 'the/third/course', 'course_modes': ['honor', 'verified', 'audit'], 'mode': 'audit'}
        ]),
    )
    def test_get_all_enrollments(self, enrollments):
        for enrollment in enrollments:
            fake_data_api.add_course(enrollment['course_id'], course_modes=enrollment['course_modes'])
            api.add_enrollment(self.USERNAME, enrollment['course_id'], enrollment['mode'])
        result = api.get_enrollments(self.USERNAME)
        self.assertEqual(len(enrollments), len(result))
        for result_enrollment in result:
            self.assertIn(
                result_enrollment['course']['course_id'],
                [enrollment['course_id'] for enrollment in enrollments]
            )

    def test_update_enrollment(self):
        # Add fake course enrollment information to the fake data API
        fake_data_api.add_course(self.COURSE_ID, course_modes=['honor', 'verified', 'audit'])
        # Enroll in the course and verify the URL we get sent to
        result = api.add_enrollment(self.USERNAME, self.COURSE_ID, mode='audit')
        get_result = api.get_enrollment(self.USERNAME, self.COURSE_ID)
        self.assertEquals(result, get_result)

        result = api.update_enrollment(self.USERNAME, self.COURSE_ID, mode='honor')
        self.assertEquals('honor', result['mode'])

        result = api.update_enrollment(self.USERNAME, self.COURSE_ID, mode='verified')
        self.assertEquals('verified', result['mode'])

    def test_update_enrollment_attributes(self):
        # Add fake course enrollment information to the fake data API
        fake_data_api.add_course(self.COURSE_ID, course_modes=['honor', 'verified', 'audit', 'credit'])
        # Enroll in the course and verify the URL we get sent to
        result = api.add_enrollment(self.USERNAME, self.COURSE_ID, mode='audit')
        get_result = api.get_enrollment(self.USERNAME, self.COURSE_ID)
        self.assertEquals(result, get_result)

        enrollment_attributes = [
            {
                "namespace": "credit",
                "name": "provider_id",
                "value": "hogwarts",
            }
        ]

        result = api.update_enrollment(
            self.USERNAME, self.COURSE_ID, mode='credit', enrollment_attributes=enrollment_attributes
        )
        self.assertEquals('credit', result['mode'])
        attributes = api.get_enrollment_attributes(self.USERNAME, self.COURSE_ID)
        self.assertEquals(enrollment_attributes[0], attributes[0])

    def test_get_course_details(self):
        # Add a fake course enrollment information to the fake data API
        fake_data_api.add_course(self.COURSE_ID, course_modes=['honor', 'verified', 'audit'])
        result = api.get_course_enrollment_details(self.COURSE_ID)
        self.assertEquals(result['course_id'], self.COURSE_ID)
        self.assertEquals(3, len(result['course_modes']))

    @override_settings(ENROLLMENT_DATA_API='foo.bar.biz.baz')
    @raises(EnrollmentApiLoadError)
    def test_data_api_config_error(self):
        # Enroll in the course and verify the URL we get sent to
        api.add_enrollment(self.USERNAME, self.COURSE_ID, mode='audit')

    def test_caching(self):
        # Add fake course enrollment information to the fake data API
        fake_data_api.add_course(self.COURSE_ID, course_modes=['honor', 'verified', 'audit'])

        # Hit the fake data API.
        details = api.get_course_enrollment_details(self.COURSE_ID)

        # Reset the fake data API, should rely on the cache.
        fake_data_api.reset()
        cached_details = api.get_course_enrollment_details(self.COURSE_ID)

        # The data matches
        self.assertEqual(len(details['course_modes']), 3)
        self.assertEqual(details, cached_details)
