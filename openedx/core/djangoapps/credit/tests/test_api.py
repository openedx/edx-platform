"""
Tests for the API functions in the credit app.
"""
import datetime
import ddt
import pytz

from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection, transaction

from opaque_keys.edx.keys import CourseKey

from util.date_utils import from_timestamp
from openedx.core.djangoapps.credit import api
from openedx.core.djangoapps.credit.exceptions import (
    InvalidCreditRequirements,
    InvalidCreditCourse,
    RequestAlreadyCompleted,
    UserIsNotEligible,
    InvalidCreditStatus,
    CreditRequestNotFound,
)
from openedx.core.djangoapps.credit.models import (
    CreditCourse,
    CreditProvider,
    CreditRequirement,
    CreditRequirementStatus,
    CreditEligibility
)
from student.tests.factories import UserFactory


TEST_CREDIT_PROVIDER_SECRET_KEY = "931433d583c84ca7ba41784bad3232e6"


@override_settings(CREDIT_PROVIDER_SECRET_KEYS={
    "hogwarts": TEST_CREDIT_PROVIDER_SECRET_KEY,
    "ASU": TEST_CREDIT_PROVIDER_SECRET_KEY,
    "MIT": TEST_CREDIT_PROVIDER_SECRET_KEY
})
class CreditApiTestBase(TestCase):
    """
    Base class for test cases of the credit API.
    """

    PROVIDER_ID = "hogwarts"
    PROVIDER_NAME = "Hogwarts School of Witchcraft and Wizardry"
    PROVIDER_URL = "https://credit.example.com/request"
    PROVIDER_STATUS_URL = "https://credit.example.com/status"

    def setUp(self, **kwargs):
        super(CreditApiTestBase, self).setUp()
        self.course_key = CourseKey.from_string("edX/DemoX/Demo_Course")

    def add_credit_course(self, enabled=True):
        """Mark the course as a credit """
        credit_course = CreditCourse.objects.create(course_key=self.course_key, enabled=enabled)

        CreditProvider.objects.create(
            provider_id=self.PROVIDER_ID,
            display_name=self.PROVIDER_NAME,
            provider_url=self.PROVIDER_URL,
            provider_status_url=self.PROVIDER_STATUS_URL,
            enable_integration=True,
        )

        return credit_course


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

    def test_set_credit_requirement_status(self):
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

        # Initially, the status should be None
        req_status = api.get_credit_requirement_status(self.course_key, "staff", namespace="grade", name="grade")
        self.assertEqual(req_status[0]["status"], None)

        # Set the requirement to "satisfied" and check that it's actually set
        api.set_credit_requirement_status("staff", self.course_key, "grade", "grade")
        req_status = api.get_credit_requirement_status(self.course_key, "staff", namespace="grade", name="grade")
        self.assertEqual(req_status[0]["status"], "satisfied")

        # Set the requirement to "failed" and check that it's actually set
        api.set_credit_requirement_status("staff", self.course_key, "grade", "grade", status="failed")
        req_status = api.get_credit_requirement_status(self.course_key, "staff", namespace="grade", name="grade")
        self.assertEqual(req_status[0]["status"], "failed")

    def test_satisfy_all_requirements(self):
        # Configure a course with two credit requirements
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

        # Satisfy one of the requirements, but not the other
        with self.assertNumQueries(7):
            api.set_credit_requirement_status(
                "bob",
                self.course_key,
                requirements[0]["namespace"],
                requirements[0]["name"]
            )

        # The user should not be eligible (because only one requirement is satisfied)
        self.assertFalse(api.is_user_eligible_for_credit("bob", self.course_key))

        # Satisfy the other requirement
        with self.assertNumQueries(10):
            api.set_credit_requirement_status(
                "bob",
                self.course_key,
                requirements[1]["namespace"],
                requirements[1]["name"]
            )

        # Now the user should be eligible
        self.assertTrue(api.is_user_eligible_for_credit("bob", self.course_key))

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
                "status_url": self.PROVIDER_STATUS_URL,
            }
        ])

        # Disable the provider; it should be hidden from the list
        provider = CreditProvider.objects.get()
        provider.active = False
        provider.save()

        result = api.get_credit_providers()
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
        self.assertTrue(parsed_date < datetime.datetime.now(pytz.UTC))

        # Validate course information
        self.assertIn('course_org', parameters)
        self.assertEqual(parameters['course_org'], self.course_key.org)
        self.assertIn('course_num', parameters)
        self.assertEqual(parameters['course_num'], self.course_key.course)
        self.assertIn('course_run', parameters)
        self.assertEqual(parameters['course_run'], self.course_key.run)
        self.assertIn('final_grade', parameters)
        self.assertEqual(parameters['final_grade'], self.FINAL_GRADE)

        # Validate user information
        for key in self.USER_INFO.keys():
            param_key = 'user_{key}'.format(key=key)
            self.assertIn(param_key, parameters)
            self.assertEqual(parameters[param_key], self.USER_INFO[key])

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
        # - 2 queries: Update the request.
        # - 2 queries: Update the history table for the request.
        with self.assertNumQueries(10):
            request = api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO['username'])

        # - 3 queries: Retrieve and update the request
        # - 1 query: Update the history table for the request.
        uuid = request["parameters"]["request_uuid"]
        with self.assertNumQueries(4):
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
    def test_user_is_not_eligible(self, status):
        # Simulate a user who is not eligible for credit
        CreditEligibility.objects.all().delete()
        status = CreditRequirementStatus.objects.get(username=self.USER_INFO['username'])
        status.status = status
        status.reason = {}
        status.save()

        with self.assertRaises(UserIsNotEligible):
            api.create_credit_request(self.course_key, self.PROVIDER_ID, self.USER_INFO['username'])

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
        transaction.commit_unless_managed()

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

    def _configure_credit(self):
        """
        Configure a credit course and its requirements.

        By default, add a single requirement (minimum grade)
        that the user has satisfied.

        """
        credit_course = self.add_credit_course()
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
            course=CreditCourse.objects.get(course_key=self.course_key)
        )

    def _assert_credit_status(self, expected_status):
        """Check the user's credit status. """
        statuses = api.get_credit_requests_for_user(self.USER_INFO["username"])
        self.assertEqual(statuses[0]["status"], expected_status)
