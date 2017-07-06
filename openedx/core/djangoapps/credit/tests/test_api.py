"""
Tests for the API functions in the credit app.
"""
import datetime
import json
import unittest

import ddt
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.test.utils import override_settings
from django.db import connection
from nose.plugins.attrib import attr
import httpretty
from lms.djangoapps.commerce.tests import TEST_API_SIGNING_KEY, TEST_API_URL
import mock
import pytz
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.credit import api
from openedx.core.djangoapps.credit.email_utils import get_credit_provider_display_names, make_providers_strings
from openedx.core.djangoapps.credit.exceptions import (
    InvalidCreditRequirements,
    InvalidCreditCourse,
    RequestAlreadyCompleted,
    UserIsNotEligible,
    InvalidCreditStatus,
    CreditRequestNotFound,
)
from openedx.core.djangoapps.credit.models import (
    CreditConfig,
    CreditCourse,
    CreditProvider,
    CreditRequirement,
    CreditRequirementStatus,
    CreditEligibility,
    CreditRequest
)
from student.tests.factories import UserFactory
from util.date_utils import from_timestamp
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


TEST_CREDIT_PROVIDER_SECRET_KEY = "931433d583c84ca7ba41784bad3232e6"
TEST_ECOMMERCE_WORKER = 'test_worker'


@override_settings(CREDIT_PROVIDER_SECRET_KEYS={
    "hogwarts": TEST_CREDIT_PROVIDER_SECRET_KEY,
    "ASU": TEST_CREDIT_PROVIDER_SECRET_KEY,
    "MIT": TEST_CREDIT_PROVIDER_SECRET_KEY
})
class CreditApiTestBase(ModuleStoreTestCase):
    """
    Base class for test cases of the credit API.
    """

    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    PROVIDER_ID = "hogwarts"
    PROVIDER_NAME = "Hogwarts School of Witchcraft and Wizardry"
    PROVIDER_URL = "https://credit.example.com/request"
    PROVIDER_STATUS_URL = "https://credit.example.com/status"
    PROVIDER_DESCRIPTION = "A new model for the Witchcraft and Wizardry School System."
    ENABLE_INTEGRATION = True
    FULFILLMENT_INSTRUCTIONS = "Sample fulfillment instruction for credit completion."
    USER_INFO = {
        "username": "bob",
        "email": "bob@example.com",
        "password": "test_bob",
        "full_name": "Bob",
        "mailing_address": "123 Fake Street, Cambridge MA",
        "country": "US",
    }
    THUMBNAIL_URL = "https://credit.example.com/logo.png"

    PROVIDERS_LIST = [u'Hogwarts School of Witchcraft and Wizardry', u'Arizona State University']

    COURSE_API_RESPONSE = {
        "id": "course-v1:Demo+Demox+Course",
        "url": "http://localhost/api/v2/courses/course-v1:Demo+Demox+Course/",
        "name": "dummy edX Demonstration Course",
        "verification_deadline": "2023-09-12T23:59:00Z",
        "type": "credit",
        "products_url": "http://localhost/api/v2/courses/course:Demo+Demox+Course/products/",
        "last_edited": "2016-03-06T09:51:10Z",
        "products": [
            {
                "id": 1,
                "url": "http://localhost/api/v2/products/11/",
                "structure": "child",
                "product_class": "Seat",
                "title": "",
                "price": 1,
                "expires": '2016-03-06T09:51:10Z',
                "attribute_values": [
                    {
                        "name": "certificate_type",
                        "value": "credit"
                    },
                    {
                        "name": "course_key",
                        "value": "edX/DemoX/Demo_Course",
                    },
                    {
                        "name": "credit_hours",
                        "value": 1
                    },
                    {
                        "name": "credit_provider",
                        "value": "ASU"
                    },
                    {
                        "name": "id_verification_required",
                        "value": False
                    }
                ],
                "is_available_to_buy": False,
                "stockrecords": []
            },
            {
                "id": 2,
                "url": "http://localhost/api/v2/products/10/",
                "structure": "child",
                "product_class": "Seat",
                "title": "",
                "price": 1,
                "expires": '2016-03-06T09:51:10Z',
                "attribute_values": [
                    {
                        "name": "certificate_type",
                        "value": "credit"
                    },
                    {
                        "name": "course_key",
                        "value": "edX/DemoX/Demo_Course",
                    },
                    {
                        "name": "credit_hours",
                        "value": 1
                    },
                    {
                        "name": "credit_provider",
                        "value": PROVIDER_ID
                    },
                    {
                        "name": "id_verification_required",
                        "value": False
                    }
                ],
                "is_available_to_buy": False,
                "stockrecords": []
            }
        ]
    }

    def setUp(self, **kwargs):
        super(CreditApiTestBase, self).setUp()
        self.course_key = CourseKey.from_string("edX/DemoX/Demo_Course")

    def add_credit_course(self, course_key=None, enabled=True):
        """Mark the course as a credit """
        course_key = course_key or self.course_key
        credit_course = CreditCourse.objects.create(course_key=course_key, enabled=enabled)

        CreditProvider.objects.get_or_create(
            provider_id=self.PROVIDER_ID,
            display_name=self.PROVIDER_NAME,
            provider_url=self.PROVIDER_URL,
            provider_status_url=self.PROVIDER_STATUS_URL,
            provider_description=self.PROVIDER_DESCRIPTION,
            enable_integration=self.ENABLE_INTEGRATION,
            fulfillment_instructions=self.FULFILLMENT_INSTRUCTIONS,
            thumbnail_url=self.THUMBNAIL_URL
        )

        return credit_course

    def _mock_ecommerce_courses_api(self, course_key, body, status=200):
        """ Mock GET requests to the ecommerce course API endpoint. """
        httpretty.reset()
        httpretty.register_uri(
            httpretty.GET, '{}/courses/{}/?include_products=1'.format(TEST_API_URL, unicode(course_key)),
            status=status,
            body=json.dumps(body), content_type='application/json',
        )


@attr('shard_2')
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
@ddt.ddt
class CreditRequirementApiTests(CreditApiTestBase):
    """
    Test Python API for credit requirements and eligibility.
    """

    @ddt.data(
        [
            {
                "namespace": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            }
        ],
        [
            {
                "name": "grade",
                "criteria": {
                    "min_grade": 0.8
                }
            }
        ],
        [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade"
            }
        ]
    )
    def test_set_credit_requirements_invalid_requirements(self, requirements):
        self.add_credit_course()
        with self.assertRaises(InvalidCreditRequirements):
            api.set_credit_requirements(self.course_key, requirements)

    def test_set_credit_requirements_invalid_course(self):
        # Test that 'InvalidCreditCourse' exception is raise if we try to
        # set credit requirements for a non credit course.
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {},
            }
        ]
        with self.assertRaises(InvalidCreditCourse):
            api.set_credit_requirements(self.course_key, requirements)

        self.add_credit_course(enabled=False)
        with self.assertRaises(InvalidCreditCourse):
            api.set_credit_requirements(self.course_key, requirements)

    def test_set_get_credit_requirements(self):
        # Test that if same requirement is added multiple times
        self.add_credit_course()
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": 0.8
                },
            },
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": 0.9
                },
            }
        ]
        api.set_credit_requirements(self.course_key, requirements)
        self.assertEqual(len(api.get_credit_requirements(self.course_key)), 1)

    def test_disable_existing_requirement(self):
        self.add_credit_course()

        # Set initial requirements
        requirements = [
            {
                "namespace": "reverification",
                "name": "midterm",
                "display_name": "Midterm",
                "criteria": {},
            },
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": 0.8
                },
            }
        ]
        api.set_credit_requirements(self.course_key, requirements)

        # Update the requirements, removing an existing requirement
        api.set_credit_requirements(self.course_key, requirements[1:])

        # Expect that now only the grade requirement is returned
        visible_reqs = api.get_credit_requirements(self.course_key)
        self.assertEqual(len(visible_reqs), 1)
        self.assertEqual(visible_reqs[0]["namespace"], "grade")

    def test_disable_credit_requirements(self):
        self.add_credit_course()
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": 0.8
                },
            }
        ]
        api.set_credit_requirements(self.course_key, requirements)
        self.assertEqual(len(api.get_credit_requirements(self.course_key)), 1)

        requirements = [
            {
                "namespace": "reverification",
                "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                "display_name": "Assessment 1",
                "criteria": {},
            }
        ]
        api.set_credit_requirements(self.course_key, requirements)
        self.assertEqual(len(api.get_credit_requirements(self.course_key)), 1)

        grade_req = CreditRequirement.objects.filter(namespace="grade", name="grade")
        self.assertEqual(len(grade_req), 1)
        self.assertEqual(grade_req[0].active, False)

    def test_is_user_eligible_for_credit(self):
        credit_course = self.add_credit_course()
        CreditEligibility.objects.create(
            course=credit_course, username="staff"
        )
        is_eligible = api.is_user_eligible_for_credit('staff', credit_course.course_key)
        self.assertTrue(is_eligible)

        is_eligible = api.is_user_eligible_for_credit('abc', credit_course.course_key)
        self.assertFalse(is_eligible)

    def test_eligibility_expired(self):
        # Configure a credit eligibility that expired yesterday
        credit_course = self.add_credit_course()
        CreditEligibility.objects.create(
            course=credit_course,
            username="staff",
            deadline=datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=1)
        )

        # The user should NOT be eligible for credit
        is_eligible = api.is_user_eligible_for_credit("staff", credit_course.course_key)
        self.assertFalse(is_eligible)

        # The eligibility should NOT show up in the user's list of eligibilities
        eligibilities = api.get_eligibilities_for_user("staff")
        self.assertEqual(eligibilities, [])

    def test_eligibility_disabled_course(self):
        # Configure a credit eligibility for a disabled course
        credit_course = self.add_credit_course()
        credit_course.enabled = False
        credit_course.save()

        CreditEligibility.objects.create(
            course=credit_course,
            username="staff",
        )

        # The user should NOT be eligible for credit
        is_eligible = api.is_user_eligible_for_credit("staff", credit_course.course_key)
        self.assertFalse(is_eligible)

        # The eligibility should NOT show up in the user's list of eligibilities
        eligibilities = api.get_eligibilities_for_user("staff")
        self.assertEqual(eligibilities, [])

    def assert_grade_requirement_status(self, expected_status, expected_order):
        """ Assert the status and order of the grade requirement. """
        req_status = api.get_credit_requirement_status(self.course_key, 'staff', namespace="grade", name="grade")
        self.assertEqual(req_status[0]["status"], expected_status)
        self.assertEqual(req_status[0]["order"], expected_order)
        return req_status

    def test_set_credit_requirement_status(self):
        username = "staff"
        credit_course = self.add_credit_course()
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": 0.8
                },
            },
            {
                "namespace": "reverification",
                "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                "display_name": "Assessment 1",
                "criteria": {},
            }
        ]

        api.set_credit_requirements(self.course_key, requirements)
        course_requirements = api.get_credit_requirements(self.course_key)
        self.assertEqual(len(course_requirements), 2)

        # Initially, the status should be None
        self.assert_grade_requirement_status(None, 0)

        # Requirement statuses cannot be changed if a CreditRequest exists
        credit_request = CreditRequest.objects.create(
            course=credit_course,
            provider=CreditProvider.objects.first(),
            username=username,
        )
        api.set_credit_requirement_status(username, self.course_key, "grade", "grade")
        self.assert_grade_requirement_status(None, 0)
        credit_request.delete()

        # Set the requirement to "satisfied" and check that it's actually set
        api.set_credit_requirement_status(username, self.course_key, "grade", "grade")
        self.assert_grade_requirement_status('satisfied', 0)

        # Set the requirement to "failed" and check that it's actually set
        api.set_credit_requirement_status(username, self.course_key, "grade", "grade", status="failed")
        self.assert_grade_requirement_status('failed', 0)

        req_status = api.get_credit_requirement_status(self.course_key, "staff")
        self.assertEqual(req_status[0]["status"], "failed")
        self.assertEqual(req_status[0]["order"], 0)

        # make sure the 'order' on the 2nd requirement is set correctly (aka 1)
        self.assertEqual(req_status[1]["status"], None)
        self.assertEqual(req_status[1]["order"], 1)

        # Set the requirement to "declined" and check that it's actually set
        api.set_credit_requirement_status(
            username, self.course_key,
            "reverification",
            "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
            status="declined"
        )
        req_status = api.get_credit_requirement_status(
            self.course_key,
            username,
            namespace="reverification",
            name="i4x://edX/DemoX/edx-reverification-block/assessment_uuid"
        )
        self.assertEqual(req_status[0]["status"], "declined")

    def test_remove_credit_requirement_status(self):
        self.add_credit_course()
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": 0.8
                },
            },
            {
                "namespace": "reverification",
                "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                "display_name": "Assessment 1",
                "criteria": {},
            }
        ]

        api.set_credit_requirements(self.course_key, requirements)
        course_requirements = api.get_credit_requirements(self.course_key)
        self.assertEqual(len(course_requirements), 2)

        # before setting credit_requirement_status
        api.remove_credit_requirement_status("staff", self.course_key, "grade", "grade")
        req_status = api.get_credit_requirement_status(self.course_key, "staff", namespace="grade", name="grade")
        self.assertIsNone(req_status[0]["status"])
        self.assertIsNone(req_status[0]["status_date"])
        self.assertIsNone(req_status[0]["reason"])

        # Set the requirement to "satisfied" and check that it's actually set
        api.set_credit_requirement_status("staff", self.course_key, "grade", "grade")
        req_status = api.get_credit_requirement_status(self.course_key, "staff", namespace="grade", name="grade")
        self.assertEqual(len(req_status), 1)
        self.assertEqual(req_status[0]["status"], "satisfied")

        # remove the credit requirement status and check that it's actually removed
        api.remove_credit_requirement_status("staff", self.course_key, "grade", "grade")
        req_status = api.get_credit_requirement_status(self.course_key, "staff", namespace="grade", name="grade")
        self.assertIsNone(req_status[0]["status"])
        self.assertIsNone(req_status[0]["status_date"])
        self.assertIsNone(req_status[0]["reason"])

    def test_remove_credit_requirement_status_req_not_configured(self):
        # Configure a credit course with no requirements
        self.add_credit_course()

        # A user satisfies a requirement. This could potentially
        # happen if there's a lag when the requirements are removed
        # after the course is published.
        api.remove_credit_requirement_status("bob", self.course_key, "grade", "grade")

        # Since the requirement hasn't been published yet, it won't show
        # up in the list of requirements.
        req_status = api.get_credit_requirement_status(self.course_key, "bob", namespace="grade", name="grade")
        self.assertEqual(len(req_status), 0)

    @httpretty.activate
    @override_settings(
        ECOMMERCE_API_URL=TEST_API_URL,
        ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY,
        ECOMMERCE_SERVICE_WORKER_USERNAME=TEST_ECOMMERCE_WORKER
    )
    def test_satisfy_all_requirements(self):
        """ Test the credit requirements, eligibility notification, email
        content caching for a credit course.
        """
        self._mock_ecommerce_courses_api(self.course_key, self.COURSE_API_RESPONSE)
        worker_user = User.objects.create_user(username=TEST_ECOMMERCE_WORKER)
        self.assertFalse(hasattr(worker_user, 'profile'))

        # Configure a course with two credit requirements
        self.add_credit_course()
        CourseFactory.create(org='edX', number='DemoX', display_name='Demo_Course')

        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": 0.8
                },
            },
            {
                "namespace": "reverification",
                "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                "display_name": "Assessment 1",
                "criteria": {},
            }
        ]
        api.set_credit_requirements(self.course_key, requirements)

        user = UserFactory.create(username=self.USER_INFO['username'], password=self.USER_INFO['password'])

        # Satisfy one of the requirements, but not the other
        with self.assertNumQueries(12):
            api.set_credit_requirement_status(
                user.username,
                self.course_key,
                requirements[0]["namespace"],
                requirements[0]["name"]
            )

        # The user should not be eligible (because only one requirement is satisfied)
        self.assertFalse(api.is_user_eligible_for_credit("bob", self.course_key))

        # Satisfy the other requirement
        with self.assertNumQueries(20):
            api.set_credit_requirement_status(
                "bob",
                self.course_key,
                requirements[1]["namespace"],
                requirements[1]["name"]
            )

        # Now the user should be eligible
        self.assertTrue(api.is_user_eligible_for_credit("bob", self.course_key))

        # Credit eligibility email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'You are eligible for credit from Hogwarts School of Witchcraft and Wizardry'
        )

        # Now verify them email content
        email_payload_first = mail.outbox[0].attachments[0]._payload  # pylint: disable=protected-access

        # Test that email has two payloads [multipart (plain text and html
        # content), attached image]
        self.assertEqual(len(email_payload_first), 2)
        # pylint: disable=protected-access
        self.assertIn('text/plain', email_payload_first[0]._payload[0]['Content-Type'])
        # pylint: disable=protected-access
        self.assertIn('text/html', email_payload_first[0]._payload[1]['Content-Type'])
        self.assertIn('image/png', email_payload_first[1]['Content-Type'])

        # Now check that html email content has same logo image 'Content-ID'
        # as the attached logo image 'Content-ID'
        email_image = email_payload_first[1]
        html_content_first = email_payload_first[0]._payload[1]._payload  # pylint: disable=protected-access

        # strip enclosing angle brackets from 'logo_image' cache 'Content-ID'
        image_id = email_image.get('Content-ID', '')[1:-1]
        self.assertIsNotNone(image_id)
        self.assertIn(image_id, html_content_first)
        self.assertIn(
            'credit from Hogwarts School of Witchcraft and Wizardry for',
            html_content_first
        )

        # test text email contents
        text_content_first = email_payload_first[0]._payload[0]._payload
        self.assertIn(
            'credit from Hogwarts School of Witchcraft and Wizardry for',
            text_content_first
        )

        # Delete the eligibility entries and satisfy the user's eligibility
        # requirement again to trigger eligibility notification
        CreditEligibility.objects.all().delete()
        with self.assertNumQueries(16):
            api.set_credit_requirement_status(
                "bob",
                self.course_key,
                requirements[1]["namespace"],
                requirements[1]["name"]
            )

        # Credit eligibility email should be sent
        self.assertEqual(len(mail.outbox), 2)
        # Now check that on sending eligibility notification again cached
        # logo image is used
        email_payload_second = mail.outbox[1].attachments[0]._payload  # pylint: disable=protected-access
        html_content_second = email_payload_second[0]._payload[1]._payload  # pylint: disable=protected-access
        self.assertIn(image_id, html_content_second)

        # The user should remain eligible even if the requirement status is later changed
        api.set_credit_requirement_status(
            "bob",
            self.course_key,
            requirements[0]["namespace"],
            requirements[0]["name"],
            status="failed"
        )
        self.assertTrue(api.is_user_eligible_for_credit("bob", self.course_key))

    def test_set_credit_requirement_status_req_not_configured(self):
        # Configure a credit course with no requirements
        self.add_credit_course()

        # A user satisfies a requirement.  This could potentially
        # happen if there's a lag when the requirements are updated
        # after the course is published.
        api.set_credit_requirement_status("bob", self.course_key, "grade", "grade")

        # Since the requirement hasn't been published yet, it won't show
        # up in the list of requirements.
        req_status = api.get_credit_requirement_status(self.course_key, "bob", namespace="grade", name="grade")
        self.assertEqual(req_status, [])

        # Now add the requirements, simulating what happens when a course is published.
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": 0.8
                },
            },
            {
                "namespace": "reverification",
                "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                "display_name": "Assessment 1",
                "criteria": {},
            }
        ]
        api.set_credit_requirements(self.course_key, requirements)

        # The user should not have satisfied the requirements, since they weren't
        # in effect when the user completed the requirement
        req_status = api.get_credit_requirement_status(self.course_key, "bob")
        self.assertEqual(len(req_status), 2)
        self.assertEqual(req_status[0]["status"], None)
        self.assertEqual(req_status[0]["status"], None)

        # The user should *not* have satisfied the reverification requirement
        req_status = api.get_credit_requirement_status(
            self.course_key,
            "bob",
            namespace=requirements[1]["namespace"],
            name=requirements[1]["name"]
        )
        self.assertEqual(len(req_status), 1)
        self.assertEqual(req_status[0]["status"], None)

    @ddt.data(
        (
            [u'Arizona State University'],
            'credit from Arizona State University for',
            'You are eligible for credit from Arizona State University'),
        (
            [u'Arizona State University', u'Hogwarts School of Witchcraft and Wizardry'],
            'credit from Arizona State University and Hogwarts School of Witchcraft and Wizardry for',
            'You are eligible for credit from Arizona State University and Hogwarts School of Witchcraft and Wizardry'
        ),
        (
            [u'Arizona State University', u'Hogwarts School of Witchcraft and Wizardry', u'Charter Oak'],
            'credit from Arizona State University, Hogwarts School of Witchcraft and Wizardry, and Charter Oak for',
            'You are eligible for credit from Arizona State University, Hogwarts School'
            ' of Witchcraft and Wizardry, and Charter Oak'
        ),
        ([], 'credit for', 'Course Credit Eligibility'),
        (None, 'credit for', 'Course Credit Eligibility')
    )
    @ddt.unpack
    def test_eligibility_email_with_providers(self, providers_list, providers_email_message, expected_subject):
        """ Test the credit requirements, eligibility notification, email
        for different providers combinations.
        """
        # Configure a course with two credit requirements
        self.add_credit_course()
        CourseFactory.create(org='edX', number='DemoX', display_name='Demo_Course')
        requirements = [
            {
                "namespace": "grade",
                "name": "grade",
                "display_name": "Grade",
                "criteria": {
                    "min_grade": 0.8
                },
            },
            {
                "namespace": "reverification",
                "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                "display_name": "Assessment 1",
                "criteria": {},
            }
        ]
        api.set_credit_requirements(self.course_key, requirements)

        user = UserFactory.create(username=self.USER_INFO['username'], password=self.USER_INFO['password'])

        # Satisfy one of the requirements, but not the other
        api.set_credit_requirement_status(
            user.username,
            self.course_key,
            requirements[0]["namespace"],
            requirements[0]["name"]
        )
        # Satisfy the other requirement. And mocked the api to return different kind of data.
        with mock.patch('openedx.core.djangoapps.credit.email_utils.get_credit_provider_display_names') as mock_method:
            mock_method.return_value = providers_list
            api.set_credit_requirement_status(
                "bob",
                self.course_key,
                requirements[1]["namespace"],
                requirements[1]["name"]
            )
        # Now the user should be eligible
        self.assertTrue(api.is_user_eligible_for_credit("bob", self.course_key))

        # Credit eligibility email should be sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify the email subject
        self.assertEqual(mail.outbox[0].subject, expected_subject)

        # Now verify them email content
        email_payload_first = mail.outbox[0].attachments[0]._payload  # pylint: disable=protected-access
        html_content_first = email_payload_first[0]._payload[1]._payload  # pylint: disable=protected-access
        self.assertIn(providers_email_message, html_content_first)

        # test text email
        text_content_first = email_payload_first[0]._payload[0]._payload  # pylint: disable=protected-access
        self.assertIn(providers_email_message, text_content_first)


@attr('shard_2')
@ddt.ddt
class CreditProviderIntegrationApiTests(CreditApiTestBase):
    """
    Test Python API for credit provider integration.
    """

    USER_INFO = {
        "username": "bob",
        "email": "bob@example.com",
        "full_name": "Bob",
        "mailing_address": "123 Fake Street, Cambridge MA",
        "country": "US",
    }

    FINAL_GRADE = 0.95

    def setUp(self):
        super(CreditProviderIntegrationApiTests, self).setUp()
        self.user = UserFactory(
            username=self.USER_INFO['username'],
            email=self.USER_INFO['email'],
        )

        self.user.profile.name = self.USER_INFO['full_name']
        self.user.profile.mailing_address = self.USER_INFO['mailing_address']
        self.user.profile.country = self.USER_INFO['country']
        self.user.profile.save()

        # By default, configure the database so that there is a single
        # credit requirement that the user has satisfied (minimum grade)
        self._configure_credit()

    def test_get_credit_providers(self):
        # The provider should show up in the list
        result = api.get_credit_providers()
        self.assertEqual(result, [
            {
                "id": self.PROVIDER_ID,
                "display_name": self.PROVIDER_NAME,
                "url": self.PROVIDER_URL,
                "status_url": self.PROVIDER_STATUS_URL,
                "description": self.PROVIDER_DESCRIPTION,
                "enable_integration": self.ENABLE_INTEGRATION,
                "fulfillment_instructions": self.FULFILLMENT_INSTRUCTIONS,
                "thumbnail_url": self.THUMBNAIL_URL
            }
        ])

        # Disable the provider; it should be hidden from the list
        provider = CreditProvider.objects.get()
        provider.active = False
        provider.save()

        result = api.get_credit_providers()
        self.assertEqual(result, [])

    def test_get_credit_providers_details(self):
        """Test that credit api method 'test_get_credit_provider_details'
        returns dictionary data related to provided credit provider.
        """
        expected_result = [{
            "id": self.PROVIDER_ID,
            "display_name": self.PROVIDER_NAME,
            "url": self.PROVIDER_URL,
            "status_url": self.PROVIDER_STATUS_URL,
            "description": self.PROVIDER_DESCRIPTION,
            "enable_integration": self.ENABLE_INTEGRATION,
            "fulfillment_instructions": self.FULFILLMENT_INSTRUCTIONS,
            "thumbnail_url": self.THUMBNAIL_URL
        }]
        result = api.get_credit_providers([self.PROVIDER_ID])
        self.assertEqual(result, expected_result)

        # now test that user gets empty dict for non existent credit provider
        result = api.get_credit_providers(['fake_provider_id'])
        self.assertEqual(result, [])

    def test_credit_request(self):
        # Initiate a credit request
        request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO['username'])

        # Validate the URL and method
        self.assertIn('url', request)
        self.assertEqual(request['url'], self.PROVIDER_URL)
        self.assertIn('method', request)
        self.assertEqual(request['method'], "POST")

        self.assertIn('parameters', request)
        parameters = request['parameters']

        # Validate the UUID
        self.assertIn('request_uuid', parameters)
        self.assertEqual(len(parameters['request_uuid']), 32)

        # Validate the timestamp
        self.assertIn('timestamp', parameters)
        parsed_date = from_timestamp(parameters['timestamp'])
        self.assertLess(parsed_date, datetime.datetime.now(pytz.UTC))

        # Validate course information
        self.assertEqual(parameters['course_org'], self.course_key.org)
        self.assertEqual(parameters['course_num'], self.course_key.course)
        self.assertEqual(parameters['course_run'], self.course_key.run)
        self.assertEqual(parameters['final_grade'], unicode(self.FINAL_GRADE))

        # Validate user information
        for key in self.USER_INFO.keys():
            param_key = 'user_{key}'.format(key=key)
            self.assertIn(param_key, parameters)
            expected = '' if key == 'mailing_address' else self.USER_INFO[key]
            self.assertEqual(parameters[param_key], expected)

    def test_create_credit_request_grade_length(self):
        """ Verify the length of the final grade is limited to seven (7) characters total.

        This is a hack for ASU.
        """
        # Update the user's grade
        status = CreditRequirementStatus.objects.get(username=self.USER_INFO["username"])
        status.status = "satisfied"
        status.reason = {"final_grade": 1.0 / 3.0}
        status.save()

        # Initiate a credit request
        request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO['username'])
        self.assertEqual(request['parameters']['final_grade'], u'0.33333')

    def test_create_credit_request_address_empty(self):
        """ Verify the mailing address is always empty. """
        request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.user.username)
        self.assertEqual(request['parameters']['user_mailing_address'], '')

    def test_credit_request_disable_integration(self):
        CreditProvider.objects.all().update(enable_integration=False)

        # Initiate a request with automatic integration disabled
        request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO['username'])

        # We get a URL and a GET method, so we can provide students
        # with a link to the credit provider, where they can request
        # credit directly.
        self.assertIn("url", request)
        self.assertEqual(request["url"], self.PROVIDER_URL)
        self.assertIn("method", request)
        self.assertEqual(request["method"], "GET")

    @ddt.data("approved", "rejected")
    def test_credit_request_status(self, status):
        request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO["username"])

        # Initial status should be "pending"
        self._assert_credit_status("pending")

        credit_request_status = api.get_credit_request_status(self.USER_INFO['username'], self.course_key)
        self.assertEqual(credit_request_status["status"], "pending")

        # Update the status
        api.update_credit_request_status(request["parameters"]["request_uuid"], self.PROVIDER_ID, status)
        self._assert_credit_status(status)

        credit_request_status = api.get_credit_request_status(self.USER_INFO['username'], self.course_key)
        self.assertEqual(credit_request_status["status"], status)

    def test_query_counts(self):
        # Yes, this is a lot of queries, but this API call is also doing a lot of work :)
        # - 1 query: Check the user's eligibility and retrieve the credit course
        # - 1 Get the provider of the credit course.
        # - 2 queries: Get-or-create the credit request.
        # - 1 query: Retrieve user account and profile information from the user API.
        # - 1 query: Look up the user's final grade from the credit requirements table.
        # - 1 query: Look up the user's enrollment date in the course.
        # - 2 query: Look up the user's completion date in the course.
        # - 1 query: Update the request.
        # - 2 queries: Update the history table for the request.
        # - 4 Django savepoints
        with self.assertNumQueries(16):
            request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO['username'])

        # - 2 queries: Retrieve and update the request
        # - 1 query: Update the history table for the request.
        uuid = request["parameters"]["request_uuid"]
        with self.assertNumQueries(3):
            api.update_credit_request_status(uuid, self.PROVIDER_ID, "approved")

        with self.assertNumQueries(1):
            api.get_credit_requests_for_user(self.USER_INFO["username"])

    def test_reuse_credit_request(self):
        # Create the first request
        first_request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO["username"])

        # Update the user's profile information, then attempt a second request
        self.user.profile.name = "Bobby"
        self.user.profile.save()
        second_request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO["username"])

        # Request UUID should be the same
        self.assertEqual(
            first_request["parameters"]["request_uuid"],
            second_request["parameters"]["request_uuid"]
        )

        # Request should use the updated information
        self.assertEqual(second_request["parameters"]["user_full_name"], "Bobby")

    @ddt.data("approved", "rejected")
    def test_cannot_make_credit_request_after_response(self, status):
        # Create the first request
        request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO["username"])

        # Provider updates the status
        api.update_credit_request_status(request["parameters"]["request_uuid"], self.PROVIDER_ID, status)

        # Attempting a second request raises an exception
        with self.assertRaises(RequestAlreadyCompleted):
            api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO['username'])

    @ddt.data("pending", "failed")
    def test_user_is_not_eligible(self, requirement_status):
        # Simulate a user who is not eligible for credit
        CreditEligibility.objects.all().delete()
        status = CreditRequirementStatus.objects.get(username=self.USER_INFO['username'])
        status.status = requirement_status
        status.reason = {}
        status.save()

        with self.assertRaises(UserIsNotEligible):
            api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO['username'])

    def test_create_credit_request_for_second_course(self):
        # Create the first request
        first_request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO["username"])

        # Create a request for a second course
        other_course_key = CourseKey.from_string("edX/other/2015")
        self._configure_credit(course_key=other_course_key)
        second_request = api.create_credit_request(other_course_key, self.PROVIDER_ID, self.USER_INFO["username"])

        # Check that the requests have the correct course number
        self.assertEqual(first_request["parameters"]["course_num"], self.course_key.course)
        self.assertEqual(second_request["parameters"]["course_num"], other_course_key.course)

    def test_create_request_null_mailing_address(self):
        # User did not specify a mailing address
        self.user.profile.mailing_address = None
        self.user.profile.save()

        # Request should include an empty mailing address field
        request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO["username"])
        self.assertEqual(request["parameters"]["user_mailing_address"], "")

    def test_create_request_null_country(self):
        # Simulate users who registered accounts before the country field was introduced.
        # We need to manipulate the database directly because the country Django field
        # coerces None values to empty strings.
        query = "UPDATE auth_userprofile SET country = NULL WHERE id = %s"
        connection.cursor().execute(query, [str(self.user.profile.id)])

        # Request should include an empty country field
        request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO["username"])
        self.assertEqual(request["parameters"]["user_country"], "")

    def test_user_has_no_final_grade(self):
        # Simulate an error condition that should never happen:
        # a user is eligible for credit, but doesn't have a final
        # grade recorded in the eligibility requirement.
        grade_status = CreditRequirementStatus.objects.get(
            username=self.USER_INFO['username'],
            requirement__namespace="grade",
            requirement__name="grade"
        )
        grade_status.reason = {}
        grade_status.save()

        with self.assertRaises(UserIsNotEligible):
            api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO["username"])

    def test_update_invalid_credit_status(self):
        # The request status must be either "approved" or "rejected"
        request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO["username"])
        with self.assertRaises(InvalidCreditStatus):
            api.update_credit_request_status(request["parameters"]["request_uuid"], self.PROVIDER_ID, "invalid")

    def test_update_credit_request_not_found(self):
        # The request UUID must exist
        with self.assertRaises(CreditRequestNotFound):
            api.update_credit_request_status("invalid_uuid", self.PROVIDER_ID, "approved")

    def test_get_credit_requests_no_requests(self):
        requests = api.get_credit_requests_for_user(self.USER_INFO["username"])
        self.assertEqual(requests, [])

    def _configure_credit(self, course_key=None):
        """
        Configure a credit course and its requirements.

        By default, add a single requirement (minimum grade)
        that the user has satisfied.

        """
        course_key = course_key or self.course_key

        credit_course = self.add_credit_course(course_key=course_key)
        requirement = CreditRequirement.objects.create(
            course=credit_course,
            namespace="grade",
            name="grade",
            active=True
        )
        status = CreditRequirementStatus.objects.create(
            username=self.USER_INFO["username"],
            requirement=requirement,
        )
        status.status = "satisfied"
        status.reason = {"final_grade": self.FINAL_GRADE}
        status.save()

        CreditEligibility.objects.create(
            username=self.USER_INFO['username'],
            course=CreditCourse.objects.get(course_key=course_key)
        )

    def _assert_credit_status(self, expected_status):
        """Check the user's credit status. """
        statuses = api.get_credit_requests_for_user(self.USER_INFO["username"])
        self.assertEqual(statuses[0]["status"], expected_status)


@attr('shard_2')
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
@override_settings(
    ECOMMERCE_API_URL=TEST_API_URL,
    ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY,
    ECOMMERCE_SERVICE_WORKER_USERNAME=TEST_ECOMMERCE_WORKER
)
@ddt.ddt
class CourseApiTests(CreditApiTestBase):
    """Test Python API for course product information."""
    def setUp(self):
        super(CourseApiTests, self).setUp()
        self.worker_user = User.objects.create_user(username=TEST_ECOMMERCE_WORKER)
        self.add_credit_course(self.course_key)
        self.credit_config = CreditConfig(cache_ttl=100, enabled=True)
        self.credit_config.save()

        # Add another provider.
        CreditProvider.objects.get_or_create(
            provider_id='ASU',
            display_name='Arizona State University',
            provider_url=self.PROVIDER_URL,
            provider_status_url=self.PROVIDER_STATUS_URL,
            provider_description=self.PROVIDER_DESCRIPTION,
            enable_integration=self.ENABLE_INTEGRATION,
            fulfillment_instructions=self.FULFILLMENT_INSTRUCTIONS,
            thumbnail_url=self.THUMBNAIL_URL
        )
        self.assertFalse(hasattr(self.worker_user, 'profile'))

    @httpretty.activate
    def test_get_credit_provider_display_names_method(self):
        """Verify that parsed providers list is returns after getting course production information."""
        self._mock_ecommerce_courses_api(self.course_key, self.COURSE_API_RESPONSE)
        response_providers = get_credit_provider_display_names(self.course_key)
        self.assertListEqual(self.PROVIDERS_LIST, response_providers)

    @httpretty.activate
    @mock.patch('edx_rest_api_client.client.EdxRestApiClient.__init__')
    def test_get_credit_provider_display_names_method_with_exception(self, mock_init):
        """Verify that in case of any exception it logs the error and return."""
        mock_init.side_effect = Exception
        response = get_credit_provider_display_names(self.course_key)
        self.assertTrue(mock_init.called)
        self.assertEqual(response, None)

    @httpretty.activate
    def test_get_credit_provider_display_names_caching(self):
        """Verify that providers list is cached."""
        self.assertTrue(self.credit_config.is_cache_enabled)
        self._mock_ecommerce_courses_api(self.course_key, self.COURSE_API_RESPONSE)

        # Warm up the cache.
        response_providers = get_credit_provider_display_names(self.course_key)
        self.assertListEqual(self.PROVIDERS_LIST, response_providers)

        # Hit the cache.
        response_providers = get_credit_provider_display_names(self.course_key)
        self.assertListEqual(self.PROVIDERS_LIST, response_providers)

        # Verify only one request was made.
        self.assertEqual(len(httpretty.httpretty.latest_requests), 1)

    @httpretty.activate
    def test_get_credit_provider_display_names_without_caching(self):
        """Verify that providers list is not cached."""
        self.credit_config.cache_ttl = 0
        self.credit_config.save()
        self.assertFalse(self.credit_config.is_cache_enabled)

        self._mock_ecommerce_courses_api(self.course_key, self.COURSE_API_RESPONSE)

        response_providers = get_credit_provider_display_names(self.course_key)
        self.assertListEqual(self.PROVIDERS_LIST, response_providers)

        response_providers = get_credit_provider_display_names(self.course_key)
        self.assertListEqual(self.PROVIDERS_LIST, response_providers)

        self.assertEqual(len(httpretty.httpretty.latest_requests), 2)

    @httpretty.activate
    @ddt.data(
        (None, None),
        ({'products': []}, []),
        (
            {
                'products': [{'expires': '', 'attribute_values': [{'name': 'credit_provider', 'value': 'ASU'}]}]
            }, ['Arizona State University']
        ),
        (
            {
                'products': [{'expires': '', 'attribute_values': [{'name': 'namespace', 'value': 'grade'}]}]
            }, []
        ),
        (
            {
                'products': [
                    {
                        'expires': '', 'attribute_values':
                        [
                            {'name': 'credit_provider', 'value': 'ASU'},
                            {'name': 'credit_provider', 'value': 'hogwarts'},
                            {'name': 'course_type', 'value': 'credit'}
                        ]
                    }
                ]
            }, ['Hogwarts School of Witchcraft and Wizardry', 'Arizona State University']
        )
    )
    @ddt.unpack
    def test_get_provider_api_with_multiple_data(self, data, expected_data):
        self._mock_ecommerce_courses_api(self.course_key, data)
        response_providers = get_credit_provider_display_names(self.course_key)
        self.assertEqual(expected_data, response_providers)

    @httpretty.activate
    def test_get_credit_provider_display_names_without_providers(self):
        """Verify that if all providers are in-active than method return empty list."""
        self._mock_ecommerce_courses_api(self.course_key, self.COURSE_API_RESPONSE)
        CreditProvider.objects.all().update(active=False)
        self.assertEqual(get_credit_provider_display_names(self.course_key), [])

    @ddt.data(None, ['asu'], ['asu', 'co'], ['asu', 'co', 'mit'])
    def test_make_providers_strings(self, providers):
        """ Verify that method returns given provider list as comma separated string. """

        provider_string = make_providers_strings(providers)

        if not providers:
            self.assertEqual(provider_string, None)

        elif len(providers) == 1:
            self.assertEqual(provider_string, providers[0])

        elif len(providers) == 2:
            self.assertEqual(provider_string, 'asu and co')

        else:
            self.assertEqual(provider_string, 'asu, co, and mit')
