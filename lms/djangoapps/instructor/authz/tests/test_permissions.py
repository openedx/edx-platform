"""
Tests for the ``InstructorAuthzPermission`` DRF permission class.
"""

from unittest.mock import Mock, patch

import ddt
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator
from openedx_authz.constants.roles import COURSE_ADMIN, COURSE_STAFF
from rest_framework.test import APIRequestFactory

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.instructor.authz import constants
from lms.djangoapps.instructor.authz.permissions import InstructorAuthzPermission
from lms.djangoapps.instructor.authz.tests.mixins import InstructorAuthzTestMixin

COURSE_KEY = CourseLocator("edX", "Demo", "2026")


class FakeView:
    """Minimal view with the attributes read by the permission class."""

    def __init__(self, course_id=str(COURSE_KEY), **attrs):
        self.kwargs = {"course_id": course_id}
        for name, value in attrs.items():
            setattr(self, name, value)


@ddt.ddt
class InstructorAuthzPermissionTest(InstructorAuthzTestMixin, TestCase):
    """Checks the AuthZ and legacy paths of the permission class."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.factory = APIRequestFactory()

    def _request(self, method="get"):
        request = getattr(self.factory, method)("/")
        request.user = self.user
        return request

    def test_authz_enabled_grants_access_by_authz_role(self):
        self.assign_authz_role(self.user, COURSE_STAFF.external_key, COURSE_KEY)
        view = FakeView(authz_permission=constants.COURSES_VIEW_ENROLLMENTS, legacy_permission_check=lambda *_: False)

        assert InstructorAuthzPermission().has_permission(self._request(), view)

    def test_authz_enabled_ignores_legacy(self):
        view = FakeView(authz_permission=constants.COURSES_VIEW_ENROLLMENTS, legacy_permission_check=lambda *_: True)

        assert not InstructorAuthzPermission().has_permission(self._request(), view)

    def test_authz_disabled_uses_legacy_permission_check(self):
        self.set_authz_enabled(False)
        self.assign_authz_role(self.user, COURSE_ADMIN.external_key, COURSE_KEY)
        legacy_check = Mock(return_value=True)
        view = FakeView(authz_permission=constants.COURSES_VIEW_ENROLLMENTS, legacy_permission_check=legacy_check)

        assert InstructorAuthzPermission().has_permission(self._request(), view)
        legacy_check.assert_called_once_with(self.user, COURSE_KEY)

    def test_authz_disabled_uses_bridgekeeper_permission_name(self):
        self.set_authz_enabled(False)
        view = FakeView(authz_permission=constants.COURSES_VIEW_ENROLLMENTS, permission_name="instructor.dashboard")
        with (
            patch("lms.djangoapps.instructor.authz.legacy.get_course_by_id", return_value="course"),
            patch.object(type(self.user), "has_perm", return_value=True) as has_perm,
        ):
            assert InstructorAuthzPermission().has_permission(self._request(), view)
        has_perm.assert_called_once_with("instructor.dashboard", "course")

    @ddt.data(("get", True), ("post", False))
    @ddt.unpack
    def test_permission_per_http_method(self, method, expected):
        self.assign_authz_role(self.user, COURSE_STAFF.external_key, COURSE_KEY)
        view = FakeView(
            authz_permission={
                "GET": constants.COURSES_VIEW_COURSE_TEAM,
                # Course Staff does not hold it.
                "POST": constants.COURSES_MANAGE_COURSE_TEAM,
            }
        )

        assert InstructorAuthzPermission().has_permission(self._request(method), view) == expected

    def test_method_missing_from_mapping_uses_legacy(self):
        view = FakeView(
            authz_permission={"GET": constants.COURSES_VIEW_COURSE_TEAM}, legacy_permission_check=lambda *_: True
        )

        assert InstructorAuthzPermission().has_permission(self._request("delete"), view)

    def test_invalid_course_key(self):
        view = FakeView(course_id="not-a-course", authz_permission=constants.COURSES_VIEW_ENROLLMENTS)

        with pytest.raises(Http404):
            InstructorAuthzPermission().has_permission(self._request(), view)

    def test_view_without_authz_permission(self):
        with pytest.raises(ImproperlyConfigured):
            InstructorAuthzPermission().has_permission(self._request(), FakeView())
