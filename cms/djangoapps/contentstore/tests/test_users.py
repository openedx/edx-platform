"""
Tests for user.py.
"""
import json
import mock
from .utils import CourseTestCase
from django.core.urlresolvers import reverse
from contentstore.views.user import _get_course_creator_status
from course_creators.views import add_user_with_status_granted
from course_creators.admin import CourseCreatorAdmin
from course_creators.models import CourseCreator

from django.http import HttpRequest
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite


class UsersTestCase(CourseTestCase):
    def setUp(self):
        super(UsersTestCase, self).setUp()
        self.url = reverse("add_user", kwargs={"location": ""})

    def test_empty(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, 400)
        content = json.loads(resp.content)
        self.assertEqual(content["Status"], "Failed")


class IndexCourseCreatorTests(CourseTestCase):
    """
    Tests the various permutations of course creator status.
    """
    def setUp(self):
        super(IndexCourseCreatorTests, self).setUp()

        self.index_url = reverse("index")
        self.request_access_url = reverse("request_course_creator")

        # Disable course creation takes precedence over enable creator group. I have enabled the
        # latter to make this clear.
        self.disable_course_creation = {
            "DISABLE_COURSE_CREATION": True,
            "ENABLE_CREATOR_GROUP": True,
            'STUDIO_REQUEST_EMAIL': 'mark@marky.mark',
        }

        self.enable_creator_group = {"ENABLE_CREATOR_GROUP": True}

        self.admin = User.objects.create_user('Mark', 'mark+courses@edx.org', 'foo')
        self.admin.is_staff = True

    def test_get_course_creator_status_disable_creation(self):
        # DISABLE_COURSE_CREATION is True (this is the case on edx, where we have a marketing site).
        # Only edx staff can create courses.
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', self.disable_course_creation):
            self.assertTrue(self.user.is_staff)
            self.assertEquals('granted', _get_course_creator_status(self.user))
            self._set_user_non_staff()
            self.assertFalse(self.user.is_staff)
            self.assertEquals('disallowed_for_this_site', _get_course_creator_status(self.user))

    def test_get_course_creator_status_default_cause(self):
        # Neither ENABLE_CREATOR_GROUP nor DISABLE_COURSE_CREATION are enabled. Anyone can create a course.
        self.assertEquals('granted', _get_course_creator_status(self.user))
        self._set_user_non_staff()
        self.assertEquals('granted', _get_course_creator_status(self.user))

    def test_get_course_creator_status_creator_group(self):
        # ENABLE_CREATOR_GROUP is True. This is the case on edge.
        # Only staff members and users who have been granted access can create courses.
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', self.enable_creator_group):
            # Staff members can always create courses.
            self.assertEquals('granted', _get_course_creator_status(self.user))
            # Non-staff must request access.
            self._set_user_non_staff()
            self.assertEquals('unrequested', _get_course_creator_status(self.user))
            # Staff user requests access.
            self.client.post(self.request_access_url)
            self.assertEquals('pending', _get_course_creator_status(self.user))

    def test_get_course_creator_status_creator_group_granted(self):
        # ENABLE_CREATOR_GROUP is True. This is the case on edge.
        # Check return value for a non-staff user who has been granted access.
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', self.enable_creator_group):
            self._set_user_non_staff()
            add_user_with_status_granted(self.admin, self.user)
            self.assertEquals('granted', _get_course_creator_status(self.user))

    def test_get_course_creator_status_creator_group_denied(self):
        # ENABLE_CREATOR_GROUP is True. This is the case on edge.
        # Check return value for a non-staff user who has been denied access.
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', self.enable_creator_group):
            self._set_user_non_staff()
            self._set_user_denied()
            self.assertEquals('denied', _get_course_creator_status(self.user))

    def test_disable_course_creation_enabled_non_staff(self):
        # Test index page content when DISABLE_COURSE_CREATION is True, non-staff member.
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', self.disable_course_creation):
            self._set_user_non_staff()
            self._assert_cannot_create()

    def test_disable_course_creation_enabled_staff(self):
        # Test index page content when DISABLE_COURSE_CREATION is True, staff member.
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', self.disable_course_creation):
            resp = self._assert_can_create()
            self.assertFalse('Email staff to create course' in resp.content)

    def test_can_create_by_default(self):
        # Test index page content with neither ENABLE_CREATOR_GROUP nor DISABLE_COURSE_CREATION enabled.
        # Anyone can create a course.
        self._assert_can_create()
        self._set_user_non_staff()
        self._assert_can_create()

    def test_course_creator_group_enabled(self):
        # Test index page content with ENABLE_CREATOR_GROUP True.
        # Staff can always create a course, others must request access.
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', self.enable_creator_group):
            # Staff members can always create courses.
            self._assert_can_create()

            # Non-staff case.
            self._set_user_non_staff()
            resp = self._assert_cannot_create()
            self.assertTrue(self.request_access_url in resp.content)

            # Now request access.
            self.client.post(self.request_access_url)

            # Still cannot create a course, but the "request access button" is no longer there.
            resp = self._assert_cannot_create()
            self.assertFalse(self.request_access_url in resp.content)
            self.assertTrue('has-status is-pending' in resp.content)

    def test_course_creator_group_granted(self):
        # Test index page content with ENABLE_CREATOR_GROUP True, non-staff member with access granted.
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', self.enable_creator_group):
            self._set_user_non_staff()
            add_user_with_status_granted(self.admin, self.user)
            self._assert_can_create()

    def test_course_creator_group_denied(self):
        # Test index page content with ENABLE_CREATOR_GROUP True, non-staff member with access denied.
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', self.enable_creator_group):
            self._set_user_non_staff()
            self._set_user_denied()
            resp = self._assert_cannot_create()
            self.assertFalse(self.request_access_url in resp.content)
            self.assertTrue('has-status is-denied' in resp.content)

    def _assert_can_create(self):
        """
        Helper method that posts to the index page and checks that the user can create a course.

        Returns the response from the post.
        """
        resp = self.client.post(self.index_url)
        self.assertTrue('new-course-button' in resp.content)
        self.assertFalse(self.request_access_url in resp.content)
        self.assertFalse('Email staff to create course' in resp.content)
        return resp

    def _assert_cannot_create(self):
        """
        Helper method that posts to the index page and checks that the user cannot create a course.

        Returns the response from the post.
        """
        resp = self.client.post(self.index_url)
        self.assertFalse('new-course-button' in resp.content)
        return resp

    def _set_user_non_staff(self):
        """
        Sets user as non-staff.
        """
        self.user.is_staff = False
        self.user.save()

    def _set_user_denied(self):
        """
        Sets course creator status to denied in admin table.
        """
        self.table_entry = CourseCreator(user=self.user)
        self.table_entry.save()

        self.deny_request = HttpRequest()
        self.deny_request.user = self.admin

        self.creator_admin = CourseCreatorAdmin(self.table_entry, AdminSite())

        self.table_entry.state = CourseCreator.DENIED
        self.creator_admin.save_model(self.deny_request, self.table_entry, None, True)
