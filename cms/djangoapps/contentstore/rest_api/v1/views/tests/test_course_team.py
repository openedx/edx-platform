"""
Unit tests for course team.
"""

import ddt
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.models.user import CourseAccessRole
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from common.djangoapps.student.tests.factories import TEST_PASSWORD, AdminFactory, UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

from ...mixins import PermissionAccessMixin


@ddt.ddt
class CourseTeamViewTest(CourseTestCase, PermissionAccessMixin):
    """
    Tests for CourseTeamView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "cms.djangoapps.contentstore:v1:course_team",
            kwargs={"course_id": self.course.id},
        )

    def get_expected_course_data(self, instructor=None, staff=None):
        """Utils is used to get expected data for course team"""
        users = []

        if instructor:
            users.append(
                {
                    "email": instructor.email,
                    "id": instructor.id,
                    "role": "instructor",
                    "username": instructor.username,
                }
            )

        if staff:
            users.append(
                {
                    "email": staff.email,
                    "id": staff.id,
                    "role": "staff",
                    "username": staff.username,
                }
            )

        return {
            "show_transfer_ownership_hint": False,
            "users": users,
            "allow_actions": True,
        }

    def create_course_user_roles(self, course_id):
        """Get course staff and instructor roles user"""
        instructor = UserFactory()
        CourseInstructorRole(course_id).add_users(instructor)
        staff = UserFactory()
        CourseStaffRole(course_id).add_users(staff)

        return instructor, staff

    def test_course_team_response(self):
        """Check successful response content"""
        response = self.client.get(self.url)
        expected_response = self.get_expected_course_data()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    def test_users_response(self):
        """Test the response for users in the course."""
        instructor, staff = self.create_course_user_roles(self.course.id)
        response = self.client.get(self.url)
        users_response = [dict(item) for item in response.data["users"]]
        expected_response = self.get_expected_course_data(instructor, staff)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(expected_response["users"], users_response)


@ddt.ddt
class CourseTeamManagementAPIViewTest(CourseTestCase):
    """
    Tests for CourseTeamManagementAPIView (org-wide, admin-only, paginated, user-role-in-courses API).
    """

    def setUp(self):
        super().setUp()
        self.admin = AdminFactory()
        self.user = UserFactory()
        self.org = "TestOrg"
        self.client = APIClient()
        self.url = reverse("cms.djangoapps.contentstore:v1:course_team_manage")
        self.client.login(username=self.admin.username, password=TEST_PASSWORD)

        # Create mock CourseOverview objects directly for testing
        self.extra_courses = [
            CourseOverviewFactory.create(
                org=self.org, run=f"CS10{i}", display_name=f"Test-Course-{i}"
            )
            for i in range(3)
        ]

        # Assign roles to user for two courses
        CourseInstructorRole(self.extra_courses[0].id).add_users(self.user)
        CourseStaffRole(self.extra_courses[0].id).add_users(self.user)
        CourseStaffRole(self.extra_courses[1].id).add_users(self.user)

    @ddt.data(
        ("instructor", "instructor"),
        ("staff", "staff"),
    )
    @ddt.unpack
    def test_admin_can_fetch_paginated_course_list_with_roles(
        self, assigned_role, expected_role
    ):
        """
        Parameterized test: checks that the correct role is returned for each course.
        """

        # Remove all roles for user in all org courses
        CourseAccessRole.objects.filter(user=self.user, org=self.org).delete()

        # Assign role if specified
        if assigned_role == "instructor":
            CourseInstructorRole(self.extra_courses[0].id).add_users(self.user)
        elif assigned_role == "staff":
            CourseStaffRole(self.extra_courses[0].id).add_users(self.user)

        response = self.client.get(
            self.url, {"org": self.org, "email": self.user.email}
        )
        self.assertEqual(response.status_code, 200)

        course_found = False
        for course in response.data["results"]:
            if course["course_id"] == str(self.extra_courses[0].id):
                with self.subTest(
                    assigned_role=assigned_role, expected_role=expected_role
                ):
                    self.assertEqual(course["role"], expected_role)
                course_found = True
        self.assertTrue(course_found, "Course not found in response.")

    def test_missing_org_or_email_returns_400(self):
        resp1 = self.client.get(self.url, {"org": self.org})
        resp2 = self.client.get(self.url, {"email": self.user.email})
        self.assertEqual(resp1.status_code, 400)
        self.assertEqual(resp2.status_code, 400)

    def test_nonexistent_user_returns_404(self):
        resp = self.client.get(
            self.url, {"org": self.org, "email": "notfound@example.com"}
        )
        self.assertEqual(resp.status_code, 404)

    def test_non_admin_user_forbidden(self):
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        resp = self.client.get(self.url, {"org": self.org, "email": self.user.email})
        self.assertEqual(resp.status_code, 403)

    def test_pagination_works(self):
        resp = self.client.get(
            self.url,
            {"org": self.org, "email": self.user.email, "page": 1, "page_size": 2},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 2)
        self.assertIsNotNone(resp.data["next"])
        resp2 = self.client.get(resp.data["next"])
        self.assertEqual(resp2.status_code, 200)

    def test_user_with_no_roles(self):
        new_user = UserFactory()
        resp = self.client.get(self.url, {"org": self.org, "email": new_user.email})
        self.assertEqual(resp.status_code, 200)
        for course in resp.data["results"]:
            self.assertIsNone(course["role"])
        course_ids = [c["course_id"] for c in resp.data["results"]]
        expected_ids = [str(ec.id) for ec in self.extra_courses]
        self.assertSetEqual(set(course_ids), set(expected_ids))

    def test_instructor_and_staff_role_prefers_instructor(self):
        # If user has both instructor and staff roles in a course, response should show 'instructor'.
        resp = self.client.get(self.url, {"org": self.org, "email": self.user.email})
        self.assertEqual(resp.status_code, 200)
        for course in resp.data["results"]:
            if course["course_id"] == str(self.extra_courses[0].id):
                self.assertEqual(course["role"], "instructor")

    # --- PUT API TEST CASES ---
    def test_bulk_role_api_empty_list_returns_400(self):
        """
        Bulk role API: sending an empty list returns a 400 with a proper error message.
        """
        resp = self.client.put(self.url, [], format="json")
        self.assertEqual(resp.status_code, 400)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertIn("list", result["error"])

    def test_bulk_role_api_non_list_input_returns_400(self):
        """
        Bulk role API: sending a non-list (e.g., dict) returns a 400 with a proper error message.
        """
        resp = self.client.put(self.url, {"email": "foo@bar.com"}, format="json")
        self.assertEqual(resp.status_code, 400)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertIn("list", result["error"])

    def test_bulk_role_api_missing_fields(self):
        """
        Test that missing required fields in the PUT API request returns an error.
        """
        data = [{"email": "", "course_id": "", "role": "", "action": ""}]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertIn("email", result)
        self.assertIn("course_id", result)
        self.assertIn("role", result)
        self.assertIn("action", result)

    def test_bulk_role_api_invalid_user(self):
        """
        Test that providing an invalid user email in the PUT API request returns an error.
        """
        data = [
            {
                "email": "notfound@example.com",
                "course_id": str(self.extra_courses[0].id),
                "role": "instructor",
                "action": "assign",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertIn("email", result)
        self.assertIn("course_id", result)
        self.assertIn("role", result)
        self.assertIn("action", result)

    def test_bulk_role_api_invalid_course_id(self):
        """
        Test that providing an invalid course_id in the PUT API request returns an error.
        """
        target_user = UserFactory()
        data = [
            {
                "email": target_user.email,
                "course_id": "invalid-course-id",
                "role": "instructor",
                "action": "assign",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertIn("email", result)
        self.assertIn("course_id", result)
        self.assertIn("role", result)
        self.assertIn("action", result)

    def test_bulk_role_api_invalid_action(self):
        """
        Test that providing an invalid action in the PUT API request returns an error.
        """
        target_user = UserFactory()
        course = self.extra_courses[0]
        data = [
            {
                "email": target_user.email,
                "course_id": str(course.id),
                "role": "instructor",
                "action": "not_a_valid_action",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertIn("email", result)
        self.assertIn("course_id", result)
        self.assertIn("role", result)
        self.assertIn("action", result)

    def assert_enrolled(self, user, course_id):
        self.assertTrue(
            CourseEnrollment.is_enrolled(user, course_id),
            f"User {user} should have been enrolled in the course",
        )

    def test_bulk_role_api_revoke_role_removes_user(self):
        """
        Bulk role API: revoking a role via the PUT API removes the user from the course team.
        """
        target_user = UserFactory()
        course = self.extra_courses[1]
        CourseStaffRole(course.id).add_users(target_user)
        data = [
            {
                "email": target_user.email,
                "course_id": str(course.id),
                "role": "staff",
                "action": "revoke",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["results"][0]["status"], "success")
        self.assertFalse(CourseStaffRole(course.id).has_user(target_user))

    def test_bulk_role_api_assign_role_enrolls_user(self):
        """
        Bulk role API: assigning a role via the PUT API also enrolls the user in the course.
        Verifies both the role assignment and the enrollment using CourseEnrollment.is_enrolled.
        """
        target_user = UserFactory()
        course = self.extra_courses[2]
        data = [
            {
                "email": target_user.email,
                "course_id": str(course.id),
                "role": "instructor",
                "action": "assign",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["results"][0]["status"], "success")
        # Check that the role was assigned
        self.assertTrue(CourseInstructorRole(course.id).has_user(target_user))
        # Check that the user is enrolled in the course
        self.assert_enrolled(target_user, course.id)
