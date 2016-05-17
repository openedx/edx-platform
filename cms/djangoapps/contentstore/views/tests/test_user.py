"""
Tests for contentstore/views/user.py.
"""
import json

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from student.roles import CourseStaffRole, CourseInstructorRole
from student import auth


class UsersTestCase(CourseTestCase):
    def setUp(self):
        super(UsersTestCase, self).setUp()
        self.ext_user = User.objects.create_user(
            "joe", "joe@comedycentral.com", "haha")
        self.ext_user.is_active = True
        self.ext_user.is_staff = False
        self.ext_user.save()
        self.inactive_user = User.objects.create_user(
            "carl", "carl@comedycentral.com", "haha")
        self.inactive_user.is_active = False
        self.inactive_user.is_staff = False
        self.inactive_user.save()

        self.index_url = self.course_team_url()
        self.detail_url = self.course_team_url(email=self.ext_user.email)
        self.inactive_detail_url = self.course_team_url(email=self.inactive_user.email)
        self.invalid_detail_url = self.course_team_url(email='nonexistent@user.com')

    def course_team_url(self, email=None):
        return reverse_course_url(
            'course_team_handler', self.course.id,
            kwargs={'email': email} if email else {}
        )

    def test_index(self):
        resp = self.client.get(self.index_url, HTTP_ACCEPT='text/html')
        # ext_user is not currently a member of the course team, and so should
        # not show up on the page.
        self.assertNotContains(resp, self.ext_user.email)

    def test_index_member(self):
        auth.add_users(self.user, CourseStaffRole(self.course.id), self.ext_user)

        resp = self.client.get(self.index_url, HTTP_ACCEPT='text/html')
        self.assertContains(resp, self.ext_user.email)

    def test_detail(self):
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertEqual(result["role"], None)
        self.assertTrue(result["active"])

    def test_detail_inactive(self):
        resp = self.client.get(self.inactive_detail_url)
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertFalse(result["active"])

    def test_detail_invalid(self):
        resp = self.client.get(self.invalid_detail_url)
        self.assertEqual(resp.status_code, 404)
        result = json.loads(resp.content)
        self.assertIn("error", result)

    def test_detail_post(self):
        resp = self.client.post(
            self.detail_url,
            data={"role": ""},
        )
        self.assertEqual(resp.status_code, 204)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        # no content: should not be in any roles
        self.assertFalse(auth.user_has_role(ext_user, CourseStaffRole(self.course.id)))
        self.assertFalse(auth.user_has_role(ext_user, CourseInstructorRole(self.course.id)))
        self.assert_not_enrolled()

    def test_detail_post_staff(self):
        resp = self.client.post(
            self.detail_url,
            data=json.dumps({"role": "staff"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 204)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        self.assertTrue(auth.user_has_role(ext_user, CourseStaffRole(self.course.id)))
        self.assertFalse(auth.user_has_role(ext_user, CourseInstructorRole(self.course.id)))
        self.assert_enrolled()

    def test_detail_post_staff_other_inst(self):
        auth.add_users(self.user, CourseInstructorRole(self.course.id), self.user)

        resp = self.client.post(
            self.detail_url,
            data=json.dumps({"role": "staff"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 204)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        self.assertTrue(auth.user_has_role(ext_user, CourseStaffRole(self.course.id)))
        self.assertFalse(auth.user_has_role(ext_user, CourseInstructorRole(self.course.id)))
        self.assert_enrolled()
        # check that other user is unchanged
        user = User.objects.get(email=self.user.email)
        self.assertTrue(auth.user_has_role(user, CourseInstructorRole(self.course.id)))
        self.assertFalse(CourseStaffRole(self.course.id).has_user(user))

    def test_detail_post_instructor(self):
        resp = self.client.post(
            self.detail_url,
            data=json.dumps({"role": "instructor"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 204)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        self.assertTrue(auth.user_has_role(ext_user, CourseInstructorRole(self.course.id)))
        self.assertFalse(CourseStaffRole(self.course.id).has_user(ext_user))
        self.assert_enrolled()

    def test_detail_post_missing_role(self):
        resp = self.client.post(
            self.detail_url,
            data=json.dumps({"toys": "fun"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.content)
        self.assertIn("error", result)
        self.assert_not_enrolled()

    def test_detail_post_no_json(self):
        resp = self.client.post(
            self.detail_url,
            data={"role": "staff"},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 204)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        self.assertTrue(auth.user_has_role(ext_user, CourseStaffRole(self.course.id)))
        self.assertFalse(auth.user_has_role(ext_user, CourseInstructorRole(self.course.id)))
        self.assert_enrolled()

    def test_detail_delete_staff(self):
        auth.add_users(self.user, CourseStaffRole(self.course.id), self.ext_user)

        resp = self.client.delete(
            self.detail_url,
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 204)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        self.assertFalse(auth.user_has_role(ext_user, CourseStaffRole(self.course.id)))

    def test_detail_delete_instructor(self):
        auth.add_users(self.user, CourseInstructorRole(self.course.id), self.ext_user, self.user)

        resp = self.client.delete(
            self.detail_url,
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 204)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        self.assertFalse(auth.user_has_role(ext_user, CourseInstructorRole(self.course.id)))

    def test_delete_last_instructor(self):
        auth.add_users(self.user, CourseInstructorRole(self.course.id), self.ext_user)

        resp = self.client.delete(
            self.detail_url,
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.content)
        self.assertIn("error", result)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        self.assertTrue(auth.user_has_role(ext_user, CourseInstructorRole(self.course.id)))

    def test_post_last_instructor(self):
        auth.add_users(self.user, CourseInstructorRole(self.course.id), self.ext_user)

        resp = self.client.post(
            self.detail_url,
            data={"role": "staff"},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.content)
        self.assertIn("error", result)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        self.assertTrue(auth.user_has_role(ext_user, CourseInstructorRole(self.course.id)))

    def test_permission_denied_self(self):
        auth.add_users(self.user, CourseStaffRole(self.course.id), self.user)
        self.user.is_staff = False
        self.user.save()

        self_url = self.course_team_url(email=self.user.email)

        resp = self.client.post(
            self_url,
            data={"role": "instructor"},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 403)
        result = json.loads(resp.content)
        self.assertIn("error", result)

    def test_permission_denied_other(self):
        auth.add_users(self.user, CourseStaffRole(self.course.id), self.user)
        self.user.is_staff = False
        self.user.save()

        resp = self.client.post(
            self.detail_url,
            data={"role": "instructor"},
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 403)
        result = json.loads(resp.content)
        self.assertIn("error", result)

    def test_staff_can_delete_self(self):
        auth.add_users(self.user, CourseStaffRole(self.course.id), self.user)
        self.user.is_staff = False
        self.user.save()

        self_url = self.course_team_url(email=self.user.email)

        resp = self.client.delete(self_url)
        self.assertEqual(resp.status_code, 204)
        # reload user from DB
        user = User.objects.get(email=self.user.email)
        self.assertFalse(auth.user_has_role(user, CourseStaffRole(self.course.id)))

    def test_staff_cannot_delete_other(self):
        auth.add_users(self.user, CourseStaffRole(self.course.id), self.user, self.ext_user)
        self.user.is_staff = False
        self.user.save()

        resp = self.client.delete(self.detail_url)
        self.assertEqual(resp.status_code, 403)
        result = json.loads(resp.content)
        self.assertIn("error", result)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        self.assertTrue(auth.user_has_role(ext_user, CourseStaffRole(self.course.id)))

    def test_user_not_initially_enrolled(self):
        # Verify that ext_user is not enrolled in the new course before being added as a staff member.
        self.assert_not_enrolled()

    def test_remove_staff_does_not_unenroll(self):
        # Add user with staff permissions.
        self.client.post(
            self.detail_url,
            data=json.dumps({"role": "staff"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assert_enrolled()
        # Remove user from staff on course. Will not un-enroll them from the course.
        resp = self.client.delete(
            self.detail_url,
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 204)
        self.assert_enrolled()

    def test_staff_to_instructor_still_enrolled(self):
        # Add user with staff permission.
        self.client.post(
            self.detail_url,
            data=json.dumps({"role": "staff"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assert_enrolled()
        # Now add with instructor permission. Verify still enrolled.
        resp = self.client.post(
            self.detail_url,
            data=json.dumps({"role": "instructor"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 204)
        self.assert_enrolled()

    def assert_not_enrolled(self):
        """ Asserts that self.ext_user is not enrolled in self.course. """
        self.assertFalse(
            CourseEnrollment.is_enrolled(self.ext_user, self.course.id),
            'Did not expect ext_user to be enrolled in course'
        )

    def assert_enrolled(self):
        """ Asserts that self.ext_user is enrolled in self.course. """
        self.assertTrue(
            CourseEnrollment.is_enrolled(self.ext_user, self.course.id),
            'User ext_user should have been enrolled in the course'
        )
