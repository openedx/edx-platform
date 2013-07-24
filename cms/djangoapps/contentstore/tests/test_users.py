import json
from .utils import CourseTestCase
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from auth.authz import get_course_groupname_for_role


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

        self.index_url = reverse("manage_users", kwargs={
            "org": self.course.location.org,
            "course": self.course.location.course,
            "name": self.course.location.name,
        })
        self.detail_url = reverse("course_team_user", kwargs={
            "org": self.course.location.org,
            "course": self.course.location.course,
            "name": self.course.location.name,
            "email": self.ext_user.email,
        })
        self.inactive_detail_url = reverse("course_team_user", kwargs={
            "org": self.course.location.org,
            "course": self.course.location.course,
            "name": self.course.location.name,
            "email": self.inactive_user.email,
        })
        self.invalid_detail_url = reverse("course_team_user", kwargs={
            "org": self.course.location.org,
            "course": self.course.location.course,
            "name": self.course.location.name,
            "email": "nonexistent@user.com",
        })
        self.staff_groupname = get_course_groupname_for_role(self.course.location, "staff")
        self.inst_groupname = get_course_groupname_for_role(self.course.location, "instructor")

    def test_index(self):
        resp = self.client.get(self.index_url)
        # ext_user is not currently a member of the course team, and so should
        # not show up on the page.
        self.assertNotContains(resp, self.ext_user.email)

    def test_index_member(self):
        group, _ = Group.objects.get_or_create(name=self.staff_groupname)
        self.ext_user.groups.add(group)
        self.ext_user.save()

        resp = self.client.get(self.index_url)
        self.assertContains(resp, self.ext_user.email)

    def test_detail(self):
        resp = self.client.get(self.detail_url)
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertEqual(result["role"], None)
        self.assertTrue(result["active"])

    def test_detail_inactive(self):
        resp = self.client.get(self.inactive_detail_url)
        self.assert2XX(resp.status_code)
        result = json.loads(resp.content)
        self.assertFalse(result["active"])

    def test_detail_invalid(self):
        resp = self.client.get(self.invalid_detail_url)
        self.assert4XX(resp.status_code)
        result = json.loads(resp.content)
        self.assertIn("error", result)

    def test_detail_post(self):
        resp = self.client.post(
            self.detail_url,
            data={"role": None},
        )
        self.assert2XX(resp.status_code)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        groups = [g.name for g in ext_user.groups.all()]
        # no content: should not be in any roles
        self.assertNotIn(self.staff_groupname, groups)
        self.assertNotIn(self.inst_groupname, groups)

    def test_detail_post_staff(self):
        resp = self.client.post(
            self.detail_url,
            data=json.dumps({"role": "staff"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assert2XX(resp.status_code)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        groups = [g.name for g in ext_user.groups.all()]
        self.assertIn(self.staff_groupname, groups)
        self.assertNotIn(self.inst_groupname, groups)

    def test_detail_post_staff_other_inst(self):
        inst_group, _ = Group.objects.get_or_create(name=self.inst_groupname)
        self.user.groups.add(inst_group)
        self.user.save()

        resp = self.client.post(
            self.detail_url,
            data=json.dumps({"role": "staff"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assert2XX(resp.status_code)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        groups = [g.name for g in ext_user.groups.all()]
        self.assertIn(self.staff_groupname, groups)
        self.assertNotIn(self.inst_groupname, groups)
        # check that other user is unchanged
        user = User.objects.get(email=self.user.email)
        groups = [g.name for g in user.groups.all()]
        self.assertNotIn(self.staff_groupname, groups)
        self.assertIn(self.inst_groupname, groups)

    def test_detail_post_instructor(self):
        resp = self.client.post(
            self.detail_url,
            data=json.dumps({"role": "instructor"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assert2XX(resp.status_code)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        groups = [g.name for g in ext_user.groups.all()]
        self.assertNotIn(self.staff_groupname, groups)
        self.assertIn(self.inst_groupname, groups)

    def test_detail_post_missing_role(self):
        resp = self.client.post(
            self.detail_url,
            data=json.dumps({"toys": "fun"}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assert4XX(resp.status_code)
        result = json.loads(resp.content)
        self.assertIn("error", result)

    def test_detail_post_bad_json(self):
        resp = self.client.post(
            self.detail_url,
            data="{foo}",
            content_type="application/json",
            HTTP_ACCEPT="application/json",
        )
        self.assert4XX(resp.status_code)
        result = json.loads(resp.content)
        self.assertIn("error", result)

    def test_detail_post_no_json(self):
        resp = self.client.post(
            self.detail_url,
            data={"role": "staff"},
            HTTP_ACCEPT="application/json",
        )
        self.assert2XX(resp.status_code)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        groups = [g.name for g in ext_user.groups.all()]
        self.assertIn(self.staff_groupname, groups)
        self.assertNotIn(self.inst_groupname, groups)

    def test_detail_delete_staff(self):
        group, _ = Group.objects.get_or_create(name=self.staff_groupname)
        self.ext_user.groups.add(group)
        self.ext_user.save()

        resp = self.client.delete(
            self.detail_url,
            HTTP_ACCEPT="application/json",
        )
        self.assert2XX(resp.status_code)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        groups = [g.name for g in ext_user.groups.all()]
        self.assertNotIn(self.staff_groupname, groups)

    def test_detail_delete_instructor(self):
        group, _ = Group.objects.get_or_create(name=self.inst_groupname)
        self.user.groups.add(group)
        self.ext_user.groups.add(group)
        self.user.save()
        self.ext_user.save()

        resp = self.client.delete(
            self.detail_url,
            HTTP_ACCEPT="application/json",
        )
        self.assert2XX(resp.status_code)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        groups = [g.name for g in ext_user.groups.all()]
        self.assertNotIn(self.inst_groupname, groups)

    def test_delete_last_instructor(self):
        group, _ = Group.objects.get_or_create(name=self.inst_groupname)
        self.ext_user.groups.add(group)
        self.ext_user.save()

        resp = self.client.delete(
            self.detail_url,
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        result = json.loads(resp.content)
        self.assertIn("error", result)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        groups = [g.name for g in ext_user.groups.all()]
        self.assertIn(self.inst_groupname, groups)

    def test_post_last_instructor(self):
        group, _ = Group.objects.get_or_create(name=self.inst_groupname)
        self.ext_user.groups.add(group)
        self.ext_user.save()

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
        groups = [g.name for g in ext_user.groups.all()]
        self.assertIn(self.inst_groupname, groups)

    def test_permission_denied_self(self):
        group, _ = Group.objects.get_or_create(name=self.staff_groupname)
        self.user.groups.add(group)
        self.user.is_staff = False
        self.user.save()

        self_url = reverse("course_team_user", kwargs={
            "org": self.course.location.org,
            "course": self.course.location.course,
            "name": self.course.location.name,
            "email": self.user.email,
        })

        resp = self.client.post(
            self_url,
            data={"role": "instructor"},
            HTTP_ACCEPT="application/json",
        )
        self.assert4XX(resp.status_code)
        result = json.loads(resp.content)
        self.assertIn("error", result)

    def test_permission_denied_other(self):
        group, _ = Group.objects.get_or_create(name=self.staff_groupname)
        self.user.groups.add(group)
        self.user.is_staff = False
        self.user.save()

        resp = self.client.post(
            self.detail_url,
            data={"role": "instructor"},
            HTTP_ACCEPT="application/json",
        )
        self.assert4XX(resp.status_code)
        result = json.loads(resp.content)
        self.assertIn("error", result)

    def test_staff_can_delete_self(self):
        group, _ = Group.objects.get_or_create(name=self.staff_groupname)
        self.user.groups.add(group)
        self.user.is_staff = False
        self.user.save()

        self_url = reverse("course_team_user", kwargs={
            "org": self.course.location.org,
            "course": self.course.location.course,
            "name": self.course.location.name,
            "email": self.user.email,
        })

        resp = self.client.delete(self_url)
        self.assert2XX(resp.status_code)
        # reload user from DB
        user = User.objects.get(email=self.user.email)
        groups = [g.name for g in user.groups.all()]
        self.assertNotIn(self.staff_groupname, groups)

    def test_staff_cannot_delete_other(self):
        group, _ = Group.objects.get_or_create(name=self.staff_groupname)
        self.user.groups.add(group)
        self.user.is_staff = False
        self.user.save()
        self.ext_user.groups.add(group)
        self.ext_user.save()

        resp = self.client.delete(self.detail_url)
        self.assert4XX(resp.status_code)
        result = json.loads(resp.content)
        self.assertIn("error", result)
        # reload user from DB
        ext_user = User.objects.get(email=self.ext_user.email)
        groups = [g.name for g in ext_user.groups.all()]
        self.assertIn(self.staff_groupname, groups)
