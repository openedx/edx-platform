"""
Tests for the AuthZ enforcement of the Instructor Dashboard API v2.

They cover the tabs, ``authz_permissions`` and the migrated endpoints.
"""

from datetime import datetime
from unittest.mock import patch

import ddt
from django.urls import reverse
from openedx_authz.constants.roles import COURSE_ADMIN, COURSE_STAFF
from pytz import UTC
from rest_framework import status
from rest_framework.test import APIClient

from common.djangoapps.student.tests.factories import (
    CourseEnrollmentFactory,
    InstructorFactory,
    StaffFactory,
    UserFactory,
)
from lms.djangoapps.instructor.authz import constants
from lms.djangoapps.instructor.authz.tests.mixins import InstructorAuthzTestMixin
from openedx.core.djangoapps.course_date_signals.handlers import extract_dates
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory

HELPERS = "lms.djangoapps.instructor.authz.helpers"

# Tabs migrated to AuthZ, each with one of the permissions that show it.
MIGRATED_TABS = {tab: permissions[0] for tab, permissions in constants.TAB_PERMISSIONS.items()}

# Every (tab, permission) pair: a single permission of the tab is enough to show it.
TAB_PERMISSION_PAIRS = [
    (tab, permission) for tab, permissions in constants.TAB_PERMISSIONS.items() for permission in permissions
]


@ddt.ddt
class CourseMetadataViewAuthzTest(InstructorAuthzTestMixin, SharedModuleStoreTestCase):
    """
    ``CourseMetadataView`` tabs and permissions follow the AuthZ flag.

    With the flag on they are resolved through AuthZ, and through the legacy
    roles when it is off.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.id

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        # The Date Extensions tab is only shown when edx-when is enabled for the course.
        patcher = patch("lms.djangoapps.instructor.views.serializers_v2.is_enabled_for_course", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.url = reverse("instructor_api_v2:course_metadata", kwargs={"course_id": str(self.course_key)})

    def _get(self, user):
        self.client.force_authenticate(user=user)
        return self.client.get(self.url)

    def _tab_ids(self, response):
        return {tab["tab_id"] for tab in response.data["tabs"]}

    def test_existing_permissions_field_is_unchanged(self):
        """The legacy ``permissions`` field keeps the same keys."""
        user = self.create_user_with_authz_role(COURSE_ADMIN.external_key, self.course_key)

        response = self._get(user)

        assert response.status_code == status.HTTP_200_OK
        assert set(response.data["permissions"]) == {
            "admin",
            "instructor",
            "finance_admin",
            "sales_admin",
            "staff",
            "forum_admin",
            "data_researcher",
        }

    def test_authz_course_admin(self):
        """A Course Admin sees every migrated tab and holds every permission."""
        user = self.create_user_with_authz_role(COURSE_ADMIN.external_key, self.course_key)

        response = self._get(user)

        assert response.status_code == status.HTTP_200_OK
        assert set(MIGRATED_TABS) <= self._tab_ids(response)
        assert set(response.data["authz_permissions"]) == set(constants.INSTRUCTOR_DASHBOARD_PERMISSIONS)
        assert all(response.data["authz_permissions"].values())

    def test_authz_course_staff(self):
        """A Course Staff sees every migrated tab but cannot manage the course team."""
        user = self.create_user_with_authz_role(COURSE_STAFF.external_key, self.course_key)

        response = self._get(user)

        tabs = self._tab_ids(response)
        assert set(MIGRATED_TABS) <= tabs
        permissions = response.data["authz_permissions"]
        assert permissions[constants.COURSES_VIEW_COURSE_TEAM]
        # Course Staff does not manage the course team.
        assert not permissions[constants.COURSES_MANAGE_COURSE_TEAM]
        assert permissions[constants.COURSES_MANAGE_COHORTS]

    def test_authz_denied_overrides_legacy_roles(self):
        """
        With the flag on, AuthZ denying a legacy instructor means no access.
        """
        instructor = InstructorFactory(course_key=self.course_key)

        with patch(f"{HELPERS}.authz_api.is_user_allowed", return_value=False):
            response = self._get(instructor)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @ddt.data(*TAB_PERMISSION_PAIRS)
    @ddt.unpack
    def test_authz_tab_shown_with_any_of_its_permissions(self, tab_id, tab_permission):
        """
        A tab is shown with any one of its permissions, and hidden without all of them.
        """
        user = UserFactory()

        def allowed_only(*permissions):
            return lambda _username, permission, _scope: permission in permissions

        with patch(
            f"{HELPERS}.authz_api.is_user_allowed", side_effect=allowed_only(constants.COURSES_VIEW_COURSE_INFO)
        ):
            tabs_without_permission = self._tab_ids(self._get(user))
        with patch(
            f"{HELPERS}.authz_api.is_user_allowed",
            side_effect=allowed_only(constants.COURSES_VIEW_COURSE_INFO, tab_permission),
        ):
            tabs_with_permission = self._tab_ids(self._get(user))

        assert tab_id in tabs_with_permission
        if tab_id != "course_info":
            assert tab_id not in tabs_without_permission

    def test_legacy_instructor_sees_migrated_tabs(self):
        """With the flag off, a legacy instructor sees every migrated tab and manages the course team."""
        self.set_authz_enabled(False)
        instructor = InstructorFactory(course_key=self.course_key)

        response = self._get(instructor)

        assert response.status_code == status.HTTP_200_OK
        assert "date_extensions" in self._tab_ids(response)
        assert set(MIGRATED_TABS) <= self._tab_ids(response)
        assert response.data["authz_permissions"][constants.COURSES_MANAGE_COURSE_TEAM]

    def test_legacy_staff_has_staff_only_tabs(self):
        """
        Staff without the forum Administrator role does not see Course Team, and
        without instructor access does not see Date Extensions.
        """
        self.set_authz_enabled(False)
        staff = StaffFactory(course_key=self.course_key)

        response = self._get(staff)

        tabs = self._tab_ids(response)
        assert tabs & set(MIGRATED_TABS) == set(MIGRATED_TABS) - {"course_team", "date_extensions"}
        assert not response.data["authz_permissions"][constants.COURSES_MANAGE_COURSE_TEAM]

    def test_legacy_does_not_query_authz(self):
        """With the flag off, AuthZ is not queried."""
        self.set_authz_enabled(False)
        instructor = InstructorFactory(course_key=self.course_key)

        with patch(f"{HELPERS}.authz_api.is_user_allowed") as is_user_allowed:
            response = self._get(instructor)

        assert response.status_code == status.HTTP_200_OK
        is_user_allowed.assert_not_called()


@ddt.ddt
class DateExtensionsAuthzTest(InstructorAuthzTestMixin, SharedModuleStoreTestCase):
    """
    AuthZ enforcement of the Date Extensions tab endpoints: ``GradedSubsectionsView``
    and ``UnitExtensionsView`` (``courses.view_learner_extensions``), and
    ``ChangeDueDateView`` (``courses.manage_learner_extensions``).
    """

    # (url_name, "get" or "post")
    VIEW_ENDPOINTS = (("graded_subsections", "get"), ("unit_extensions", "get"))
    MANAGE_ENDPOINTS = (("change_due_date", "post"),)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.id
        cls.chapter = BlockFactory.create(parent=cls.course, category="chapter")
        cls.sequential = BlockFactory.create(
            parent=cls.chapter,
            category="sequential",
            due=datetime(2030, 1, 1, tzinfo=UTC),
            metadata={"graded": True, "format": "Homework"},
        )
        # ChangeDueDateView extends a date through edx-when, which needs the course's
        # dates extracted into its own store before it recognizes this due date exists.
        extract_dates(None, cls.course_key)

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.learner = UserFactory()
        CourseEnrollmentFactory.create(user=self.learner, course_id=self.course_key)

    def _request(self, user, url_name, method):
        """Call the given endpoint as ``user``, GET or POST depending on ``method``."""
        self.client.force_authenticate(user=user)
        url = reverse(f"instructor_api_v2:{url_name}", kwargs={"course_id": str(self.course_key)})
        if method == "get":
            return self.client.get(url)
        return self.client.post(
            url,
            {
                "block_id": str(self.sequential.location),
                "due_datetime": "01/01/2030 00:00",
                "email_or_username": self.learner.username,
            },
            format="json",
        )

    @ddt.data(*VIEW_ENDPOINTS, *MANAGE_ENDPOINTS)
    @ddt.unpack
    def test_authz_course_admin_has_access(self, url_name, method):
        """A Course Admin can view and manage date extensions."""
        user = self.create_user_with_authz_role(COURSE_ADMIN.external_key, self.course_key)

        response = self._request(user, url_name, method)

        assert response.status_code == status.HTTP_200_OK

    @ddt.data(*VIEW_ENDPOINTS, *MANAGE_ENDPOINTS)
    @ddt.unpack
    def test_authz_course_staff_has_access(self, url_name, method):
        """A Course Staff can view and manage date extensions."""
        user = self.create_user_with_authz_role(COURSE_STAFF.external_key, self.course_key)

        response = self._request(user, url_name, method)

        assert response.status_code == status.HTTP_200_OK

    @ddt.data(*VIEW_ENDPOINTS, *MANAGE_ENDPOINTS)
    @ddt.unpack
    def test_authz_user_without_permission_is_denied(self, url_name, method):
        """A user with no AuthZ role in the course is denied."""
        user = UserFactory()

        response = self._request(user, url_name, method)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @ddt.data(*VIEW_ENDPOINTS, *MANAGE_ENDPOINTS)
    @ddt.unpack
    def test_authz_denied_overrides_legacy_roles(self, url_name, method):
        """With the flag on, AuthZ denying a legacy instructor means no access."""
        instructor = InstructorFactory(course_key=self.course_key)

        with patch(f"{HELPERS}.authz_api.is_user_allowed", return_value=False):
            response = self._request(instructor, url_name, method)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @ddt.data(*VIEW_ENDPOINTS, *MANAGE_ENDPOINTS)
    @ddt.unpack
    def test_legacy_instructor_keeps_access(self, url_name, method):
        """With the flag off, a legacy instructor keeps the access it always had."""
        self.set_authz_enabled(False)
        instructor = InstructorFactory(course_key=self.course_key)

        response = self._request(instructor, url_name, method)

        assert response.status_code == status.HTTP_200_OK

    @ddt.data(*VIEW_ENDPOINTS, *MANAGE_ENDPOINTS)
    @ddt.unpack
    def test_legacy_student_is_denied(self, url_name, method):
        """With the flag off, an enrolled learner with no staff role is denied."""
        self.set_authz_enabled(False)

        response = self._request(self.learner, url_name, method)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_legacy_does_not_query_authz(self):
        """With the flag off, AuthZ is not queried."""
        self.set_authz_enabled(False)
        instructor = InstructorFactory(course_key=self.course_key)

        with patch(f"{HELPERS}.authz_api.is_user_allowed") as is_user_allowed:
            response = self._request(instructor, "graded_subsections", "get")

        assert response.status_code == status.HTTP_200_OK
        is_user_allowed.assert_not_called()
