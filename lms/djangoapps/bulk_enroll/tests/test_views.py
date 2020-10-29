"""
Tests for the Bulk Enrollment views.
"""


import json

import ddt
import six
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test.utils import override_settings
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from lms.djangoapps.bulk_enroll.serializers import BulkEnrollmentSerializer
from lms.djangoapps.bulk_enroll.views import BulkEnrollView
from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_id
from openedx.core.djangoapps.course_groups.tests.helpers import config_course_cohorts
from openedx.core.djangoapps.site_configuration.helpers import get_value as get_site_value
from common.djangoapps.student.models import ENROLLED_TO_UNENROLLED, UNENROLLED_TO_ENROLLED, CourseEnrollment, ManualEnrollmentAudit
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@override_settings(ENABLE_BULK_ENROLLMENT_VIEW=True)
@ddt.ddt
class BulkEnrollmentTest(ModuleStoreTestCase, LoginEnrollmentTestCase, APITestCase):
    """
    Test the bulk enrollment endpoint
    """

    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    def setUp(self):
        """ Create a course and user, then log in. """
        super(BulkEnrollmentTest, self).setUp()

        self.view = BulkEnrollView.as_view()
        self.request_factory = APIRequestFactory()
        self.url = reverse('bulk_enroll')

        self.staff = UserFactory.create(
            username=self.USERNAME,
            email=self.EMAIL,
            password=self.PASSWORD,
            is_staff=True,
        )

        self.course = CourseFactory.create()
        self.course_key = six.text_type(self.course.id)
        self.enrolled_student = UserFactory(username='EnrolledStudent', first_name='Enrolled', last_name='Student')
        CourseEnrollment.enroll(
            self.enrolled_student,
            self.course.id
        )
        self.notenrolled_student = UserFactory(username='NotEnrolledStudent', first_name='NotEnrolled',
                                               last_name='Student')

        # Email URL values
        self.site_name = get_site_value(
            'SITE_NAME',
            settings.SITE_NAME
        )
        self.about_path = '/courses/{}/about'.format(self.course.id)
        self.course_path = '/courses/{}/'.format(self.course.id)

    def request_bulk_enroll(self, data=None, use_json=False, **extra):
        """ Make an authenticated request to the bulk enrollment API. """
        content_type = None
        if use_json:
            content_type = 'application/json'
            data = json.dumps(data)
        request = self.request_factory.post(self.url, data=data, content_type=content_type, **extra)
        force_authenticate(request, user=self.staff)
        response = self.view(request)
        response.render()
        return response

    def test_course_list_serializer(self):
        """
        Test that the course serializer will work when passed a string or list.

        Internally, DRF passes the data into the value conversion method as a list instead of
        a string, so StringListField needs to work with both.
        """
        for key in [self.course_key, [self.course_key]]:
            serializer = BulkEnrollmentSerializer(data={
                'identifiers': 'percivaloctavius',
                'action': 'enroll',
                'email_students': False,
                'courses': key,
            })
            self.assertTrue(serializer.is_valid())

    def test_non_staff(self):
        """ Test that non global staff users are forbidden from API use. """
        self.staff.is_staff = False
        self.staff.save()
        response = self.request_bulk_enroll()
        self.assertEqual(response.status_code, 403)

    def test_missing_params(self):
        """ Test the response when missing all query parameters. """
        response = self.request_bulk_enroll()
        self.assertEqual(response.status_code, 400)

    def test_bad_action(self):
        """ Test the response given an invalid action """
        response = self.request_bulk_enroll({
            'identifiers': self.enrolled_student.email,
            'action': 'invalid-action',
            'courses': self.course_key,
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_email(self):
        """ Test the response given an invalid email. """
        response = self.request_bulk_enroll({
            'identifiers': 'percivaloctavius@',
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
        })
        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            'auto_enroll': False,
            'email_students': False,
            "courses": {
                self.course_key: {
                    "action": "enroll",
                    'auto_enroll': False,
                    "results": [
                        {
                            "identifier": 'percivaloctavius@',
                            "invalidIdentifier": True,
                        }
                    ]
                }
            }
        }

        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_invalid_username(self):
        """ Test the response given an invalid username. """
        response = self.request_bulk_enroll({
            'identifiers': 'percivaloctavius',
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
        })
        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            'auto_enroll': False,
            'email_students': False,
            "courses": {
                self.course_key: {
                    "action": "enroll",
                    'auto_enroll': False,
                    "results": [
                        {
                            "identifier": 'percivaloctavius',
                            "invalidIdentifier": True,
                        }
                    ]
                }
            }
        }

        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    def test_enroll_with_username(self):
        """ Test enrolling using a username as the identifier. """
        response = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.username,
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
        })
        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            'auto_enroll': False,
            "email_students": False,
            "courses": {
                self.course_key: {
                    "action": "enroll",
                    'auto_enroll': False,
                    "results": [
                        {
                            "identifier": self.notenrolled_student.username,
                            "before": {
                                "enrollment": False,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                            },
                            "after": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                            }
                        }
                    ]
                }
            }
        }
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

    @ddt.data(False, True)
    def test_enroll_with_email(self, use_json):
        """ Test enrolling using a username as the identifier. """
        response = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.email,
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
        }, use_json=use_json)
        self.assertEqual(response.status_code, 200)

        # test that the user is now enrolled
        user = User.objects.get(email=self.notenrolled_student.email)
        self.assertTrue(CourseEnrollment.is_enrolled(user, self.course.id))

        # test the response data
        expected = {
            "action": "enroll",
            "auto_enroll": False,
            "email_students": False,
            "courses": {
                self.course_key: {
                    "action": "enroll",
                    "auto_enroll": False,
                    "results": [
                        {
                            "identifier": self.notenrolled_student.email,
                            "before": {
                                "enrollment": False,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                            },
                            "after": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                            }
                        }
                    ]
                }
            }
        }

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    @ddt.data(False, True)
    def test_unenroll(self, use_json):
        """ Test unenrolling a user. """
        response = self.request_bulk_enroll({
            'identifiers': self.enrolled_student.email,
            'action': 'unenroll',
            'email_students': False,
            'courses': self.course_key,
        }, use_json=use_json)
        self.assertEqual(response.status_code, 200)

        # test that the user is now unenrolled
        user = User.objects.get(email=self.enrolled_student.email)
        self.assertFalse(CourseEnrollment.is_enrolled(user, self.course.id))

        # test the response data
        expected = {
            "action": "unenroll",
            "auto_enroll": False,
            "email_students": False,
            "courses": {
                self.course_key: {
                    "action": "unenroll",
                    "auto_enroll": False,
                    "results": [
                        {
                            "identifier": self.enrolled_student.email,
                            "before": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                            },
                            "after": {
                                "enrollment": False,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                            }
                        }
                    ]
                }
            }

        }

        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, ENROLLED_TO_UNENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)

    def test_fail_on_unequal_cohorts(self):
        """
        Test unequal items in cohorts and courses.
        """
        response = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.username,
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
            'cohorts': "cohort1,cohort2"
        })
        self.assertContains(
            response,
            'If provided, the cohorts and courses should have equal number of items.',
            status_code=400,
        )

    def test_fail_on_missing_cohorts(self):
        """
        Test cohorts don't exist in the course.
        """
        response = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.username,
            'action': 'enroll',
            'email_students': False,
            'cohorts': 'cohort1',
            'courses': self.course_key
        })
        self.assertContains(
            response,
            u'cohort {cohort_name} not found in course {course_id}.'.format(
                cohort_name='cohort1', course_id=self.course_key
            ),
            status_code=400,
        )

    def test_allow_cohorts_when_enrolling(self):
        """
        Test if the cohorts are given but the action is unenroll.
        """
        config_course_cohorts(self.course, is_cohorted=True, manual_cohorts=["cohort1", "cohort2"])
        response = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.username,
            'action': 'unenroll',
            'email_students': False,
            'cohorts': 'cohort1',
            'courses': self.course_key
        })
        self.assertContains(response, 'Cohorts can only be used for enrollments.', status_code=400)

    def test_add_to_valid_cohort(self):
        config_course_cohorts(self.course, is_cohorted=True, manual_cohorts=["cohort1", "cohort2"])
        response = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.username,
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
            'cohorts': "cohort1"
        })

        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            'auto_enroll': False,
            "email_students": False,
            "courses": {
                self.course_key: {
                    "action": "enroll",
                    'auto_enroll': False,
                    "results": [
                        {
                            "identifier": self.notenrolled_student.username,
                            "before": {
                                "enrollment": False,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": None,
                            },
                            "after": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": 'cohort1',
                            }
                        }
                    ]
                }
            }
        }
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(get_cohort_id(self.notenrolled_student, CourseKey.from_string(self.course_key)))

        self.assertEqual(res_json, expected)

    def test_readd_to_different_cohort(self):
        config_course_cohorts(self.course, is_cohorted=True, manual_cohorts=["cohort1", "cohort2"])
        response = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.username,
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
            'cohorts': "cohort1"
        })

        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            'auto_enroll': False,
            "email_students": False,
            "courses": {
                self.course_key: {
                    "action": "enroll",
                    'auto_enroll': False,
                    "results": [
                        {
                            "identifier": self.notenrolled_student.username,
                            "before": {
                                "enrollment": False,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": None,
                            },
                            "after": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": 'cohort1',
                            }
                        }
                    ]
                }
            }
        }
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(get_cohort_id(self.notenrolled_student, CourseKey.from_string(self.course_key)))
        self.assertEqual(res_json, expected)

        response2 = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.username,
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
            'cohorts': "cohort2"
        })

        self.assertEqual(response2.status_code, 200)

        # test the response data
        expected2 = {
            "action": "enroll",
            'auto_enroll': False,
            "email_students": False,
            "courses": {
                self.course_key: {
                    "action": "enroll",
                    'auto_enroll': False,
                    "results": [
                        {
                            "identifier": self.notenrolled_student.username,
                            "before": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": 'cohort1',
                            },
                            "after": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": 'cohort2',
                            }
                        }
                    ]
                }
            }
        }
        res2_json = json.loads(response2.content.decode('utf-8'))
        self.assertIsNotNone(get_cohort_id(self.notenrolled_student, CourseKey.from_string(self.course_key)))
        self.assertEqual(res2_json, expected2)

    def test_readd_to_same_cohort(self):
        config_course_cohorts(self.course, is_cohorted=True, manual_cohorts=["cohort1", "cohort2"])
        response = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.username,
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
            'cohorts': "cohort1"
        })

        self.assertEqual(response.status_code, 200)

        # test the response data
        expected = {
            "action": "enroll",
            'auto_enroll': False,
            "email_students": False,
            "courses": {
                self.course_key: {
                    "action": "enroll",
                    'auto_enroll': False,
                    "results": [
                        {
                            "identifier": self.notenrolled_student.username,
                            "before": {
                                "enrollment": False,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": None,
                            },
                            "after": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": 'cohort1',
                            }
                        }
                    ]
                }
            }
        }
        manual_enrollments = ManualEnrollmentAudit.objects.all()
        self.assertEqual(manual_enrollments.count(), 1)
        self.assertEqual(manual_enrollments[0].state_transition, UNENROLLED_TO_ENROLLED)
        res_json = json.loads(response.content.decode('utf-8'))
        self.assertIsNotNone(get_cohort_id(self.notenrolled_student, CourseKey.from_string(self.course_key)))

        self.assertEqual(res_json, expected)

        response2 = self.request_bulk_enroll({
            'identifiers': self.notenrolled_student.username,
            'action': 'enroll',
            'email_students': False,
            'courses': self.course_key,
            'cohorts': "cohort1"
        })

        self.assertEqual(response2.status_code, 200)

        # test the response data
        expected2 = {
            "action": "enroll",
            'auto_enroll': False,
            "email_students": False,
            "courses": {
                self.course_key: {
                    "action": "enroll",
                    'auto_enroll': False,
                    "results": [
                        {
                            "identifier": self.notenrolled_student.username,
                            "before": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": 'cohort1',
                            },
                            "after": {
                                "enrollment": True,
                                "auto_enroll": False,
                                "user": True,
                                "allowed": False,
                                "cohort": 'cohort1',
                            }
                        }
                    ]
                }
            }
        }
        res2_json = json.loads(response2.content.decode('utf-8'))
        self.assertIsNotNone(get_cohort_id(self.notenrolled_student, CourseKey.from_string(self.course_key)))
        self.assertEqual(res2_json, expected2)
