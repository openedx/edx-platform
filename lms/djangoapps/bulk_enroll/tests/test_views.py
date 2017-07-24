"""
Tests for the Bulk Enrollment views.
"""
import ddt
import json
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from bulk_enroll.serializers import BulkEnrollmentSerializer
from bulk_enroll.views import BulkEnrollView
from courseware.tests.helpers import LoginEnrollmentTestCase
from microsite_configuration import microsite
from student.models import (
    CourseEnrollment,
    ManualEnrollmentAudit,
    ENROLLED_TO_UNENROLLED,
    UNENROLLED_TO_ENROLLED,
)
from student.tests.factories import UserFactory
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
        self.course_key = unicode(self.course.id)
        self.enrolled_student = UserFactory(username='EnrolledStudent', first_name='Enrolled', last_name='Student')
        CourseEnrollment.enroll(
            self.enrolled_student,
            self.course.id
        )
        self.notenrolled_student = UserFactory(username='NotEnrolledStudent', first_name='NotEnrolled',
                                               last_name='Student')

        # Email URL values
        self.site_name = microsite.get_value(
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

        res_json = json.loads(response.content)
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

        res_json = json.loads(response.content)
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
        res_json = json.loads(response.content)
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
        res_json = json.loads(response.content)
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
        res_json = json.loads(response.content)
        self.assertEqual(res_json, expected)

        # Check the outbox
        self.assertEqual(len(mail.outbox), 0)
