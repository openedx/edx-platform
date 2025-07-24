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
from common.djangoapps.student.tests.factories import (
    TEST_PASSWORD,
    AdminFactory,
    InstructorFactory,
    StaffFactory,
    SuperuserFactory,
    UserFactory
)
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
    Tests for CourseTeamManagementAPIView.

    Covers:
    - GET: Viewing user's course team roles by authenticated users.
    - PUT: Assigning/revoking user roles by authorized users.
    """

    def setUp(self):
        super().setUp()
        self.staff = AdminFactory()
        self.superuser = SuperuserFactory()
        self.user = UserFactory()
        self.org = "TestOrg"
        self.client = APIClient()
        self.url = reverse("cms.djangoapps.contentstore:v1:course_team_manage")

        self.extra_courses = [
            CourseOverviewFactory.create(
                org=self.org, run=f"CS10{i}", display_name=f"Test-Course-{i}"
            )
            for i in range(3)
        ]
        self.instructor_user = InstructorFactory.create(
            course_key=self.extra_courses[0].id
        )
        self.staff_user = StaffFactory.create(course_key=self.extra_courses[1].id)

    # --- GET API TEST CASES ---

    def test_get_api_missing_email_returns_400(self):
        """GET API: Returns 400 if email parameter is missing."""
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 400)

    def test_get_api_nonexistent_user_returns_404(self):
        """GET API: Returns 404 for a nonexistent user email."""
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        resp = self.client.get(self.url, {"email": "notfound@example.com"})
        self.assertEqual(resp.status_code, 404)

    def test_get_api_unauthenticated_user_returns_401(self):
        """GET API: Unauthenticated users receive 401 Unauthorized."""
        resp = self.client.get(self.url, {"email": self.user.email})
        self.assertEqual(resp.status_code, 401)

    @ddt.data(
        ("instructor", "instructor"),
        ("staff", "staff"),
    )
    @ddt.unpack
    def test_get_api_admin_can_fetch_course_roles(self, assigned_role, expected_role):
        """GET API: Admin/staff user can view roles for any course for target user."""
        self.client.login(username=self.staff.username, password=TEST_PASSWORD)
        CourseAccessRole.objects.filter(user=self.user, org=self.org).delete()

        if assigned_role == "instructor":
            CourseInstructorRole(self.extra_courses[0].id).add_users(self.user)
        elif assigned_role == "staff":
            CourseStaffRole(self.extra_courses[0].id).add_users(self.user)

        response = self.client.get(self.url, {"email": self.user.email})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

        course_found = False
        for course in response.data:
            if course["course_id"] == str(self.extra_courses[0].id):
                with self.subTest(role=assigned_role):
                    self.assertEqual(course["role"], expected_role)
                course_found = True
        self.assertTrue(course_found, "Expected course not found in response.")

    def test_get_api_instructor_can_only_see_their_courses(self):
        """GET API: Course instructor sees only courses they have access to."""
        self.client.login(
            username=self.instructor_user.username, password=TEST_PASSWORD
        )
        resp = self.client.get(self.url, {"email": self.user.email})
        self.assertEqual(resp.status_code, 200)

        course_ids = [course["course_id"] for course in resp.data]
        self.assertIn(str(self.extra_courses[0].id), course_ids)
        for i in range(1, 3):
            self.assertNotIn(str(self.extra_courses[i].id), course_ids)

    def test_get_api_user_with_no_access_sees_no_courses(self):
        """GET API: Non-instructor users see no courses in the response."""
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        resp = self.client.get(self.url, {"email": self.user.email})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, [])

    # --- PUT API TEST CASES ---

    def test_put_api_empty_list_returns_400(self):
        """PUT API: Sending empty list returns 400 with an error message."""
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        resp = self.client.put(self.url, [], format="json")
        self.assertEqual(resp.status_code, 400)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertIn("list", result["error"])

    def test_put_api_non_list_input_returns_400(self):
        """PUT API: Sending a non-list input returns 400 with an error message."""
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        resp = self.client.put(self.url, {"email": "foo@bar.com"}, format="json")
        self.assertEqual(resp.status_code, 400)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertIn("list", result["error"])

    def test_put_api_missing_fields_returns_error(self):
        """PUT API: Request with missing required fields returns field-level errors."""
        self.client.login(
            username=self.instructor_user.username, password=TEST_PASSWORD
        )
        data = [{"email": "", "course_id": "", "role": "", "action": ""}]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        for field in ("email", "course_id", "role", "action"):
            self.assertIn(field, result)

    def test_put_api_invalid_user_email_returns_error(self):
        """PUT API: Invalid user email in request returns an error."""
        self.client.login(
            username=self.instructor_user.username, password=TEST_PASSWORD
        )
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
        self.assertIn("email", result)

    def test_put_api_invalid_course_id_returns_error(self):
        """PUT API: Invalid course_id in request returns an error."""
        self.client.login(
            username=self.instructor_user.username, password=TEST_PASSWORD
        )
        data = [
            {
                "email": self.user.email,
                "course_id": "invalid-course-id",
                "role": "instructor",
                "action": "assign",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("course_id", result)

    def test_put_api_invalid_action_returns_error(self):
        """PUT API: Invalid action value in request returns an error."""
        self.client.login(
            username=self.instructor_user.username, password=TEST_PASSWORD
        )
        data = [
            {
                "email": self.user.email,
                "course_id": str(self.extra_courses[0].id),
                "role": "instructor",
                "action": "invalid_action",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        result = resp.data["results"][0]
        self.assertEqual(result["status"], "failed")
        self.assertIn("action", result)

    def test_put_api_assign_role_enrolls_user(self):
        """PUT API: Assigning a role enrolls user in the course."""
        self.client.login(username=self.staff.username, password=TEST_PASSWORD)
        course = self.extra_courses[2]
        data = [
            {
                "email": self.user.email,
                "course_id": str(course.id),
                "role": "instructor",
                "action": "assign",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["results"][0]["status"], "success")
        self.assertTrue(CourseInstructorRole(course.id).has_user(self.user))
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course.id))

    def test_put_api_revoke_role_removes_user(self):
        """PUT API: Revoking a role removes user from course team."""
        self.client.login(username=self.staff.username, password=TEST_PASSWORD)
        course = self.extra_courses[1]
        data = [
            {
                "email": self.user.email,
                "course_id": str(course.id),
                "role": "staff",
                "action": "revoke",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["results"][0]["status"], "success")
        self.assertFalse(CourseStaffRole(course.id).has_user(self.user))

    def test_put_api_course_instructor_can_manage_own_courses(self):
        """PUT API: Course instructor can assign roles for courses they manage."""
        self.client.login(
            username=self.instructor_user.username, password=TEST_PASSWORD
        )
        data = [
            {
                "email": self.user.email,
                "course_id": str(self.extra_courses[0].id),
                "role": "staff",
                "action": "assign",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["results"][0]["status"], "success")
        self.assertTrue(CourseStaffRole(self.extra_courses[0].id).has_user(self.user))

    def test_put_api_course_instructor_cannot_manage_other_courses(self):
        """PUT API: Course instructor cannot assign roles for courses they don’t manage."""
        self.client.login(
            username=self.instructor_user.username, password=TEST_PASSWORD
        )
        data = [
            {
                "email": self.user.email,
                "course_id": str(self.extra_courses[1].id),
                "role": "staff",
                "action": "assign",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["results"][0]["status"], "failed")
        self.assertIn("do not have instructor access", resp.data["results"][0]["error"])

    def test_put_api_non_instructor_user_forbidden(self):
        """PUT API: Non-instructor users receive 403 Forbidden when assigning roles."""
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        data = [
            {
                "email": self.user.email,
                "course_id": str(self.extra_courses[0].id),
                "role": "staff",
                "action": "assign",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.data["results"][0]["status"], "failed")
        self.assertIn("do not have permission", resp.data["results"][0]["error"])

    def test_put_api_org_level_instructor_can_manage_all_org_courses(self):
        """PUT API: Org-level instructors can manage roles for all courses in their org."""
        self.client.login(
            username=self.instructor_user.username, password=TEST_PASSWORD
        )
        CourseAccessRole.objects.create(
            user=self.instructor_user, role="instructor", org=self.org, course_id=None
        )
        data = [
            {
                "email": self.user.email,
                "course_id": str(self.extra_courses[1].id),
                "role": "staff",
                "action": "assign",
            }
        ]
        resp = self.client.put(self.url, data, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["results"][0]["status"], "success")
        self.assertTrue(CourseStaffRole(self.extra_courses[1].id).has_user(self.user))
