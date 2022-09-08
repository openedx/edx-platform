"""
Tests for BridgeKeeper auth backend with get_tahoe_multitenant_auth_backends() in-use.
"""
from django.test import override_settings
from django.conf import settings

from lms.djangoapps.instructor import permissions
from lms.djangoapps.instructor.access import allow_access
from lms.djangoapps.courseware.access import has_access

from openedx.core.djangoapps.appsembler.settings.helpers import get_tahoe_multitenant_auth_backends
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@override_settings(AUTHENTICATION_BACKENDS=get_tahoe_multitenant_auth_backends(settings))
@skip_unless_lms
class TestInstructorAccessWithTahoeAuthBackends(ModuleStoreTestCase):
    """
    Ensure BridgeKeeper don't break when get_tahoe_multitenant_auth_backends() is used.

    This fixes RED-1924 in which permissions.VIEW_DASHBOARD was broken due to get_tahoe_multitenant_auth_backends().
    """

    def setUp(self):
        super(TestInstructorAccessWithTahoeAuthBackends, self).setUp()
        self.course = CourseFactory.create()
        self.instructor = UserFactory.create()
        self.staff = UserFactory.create()
        allow_access(self.course, self.instructor, 'instructor')
        allow_access(self.course, self.staff, 'staff')

    def test_tahoe_backends(self):
        """
        Ensure get_tahoe_multitenant_auth_backends adds Tahoe backends to AUTHENTICATION_BACKENDS.
        """
        assert 'tahoe_sites.backends.DefaultSiteBackend' in settings.AUTHENTICATION_BACKENDS
        assert 'tahoe_sites.backends.OrganizationMemberBackend' in settings.AUTHENTICATION_BACKENDS

    def test_instructors_has_access(self):
        """
        Sanity check for `has_access` without using BridgeKeeper's `user.has_perm()`.
        """
        assert has_access(self.staff, 'staff', self.course.id)
        assert has_access(self.instructor, 'instructor', self.course.id)

    def test_instructor_dashboard_view_perm(self):
        """
        Ensure has_perm (via BridgeKeeper) works with get_tahoe_multitenant_auth_backends() used.
        """
        assert self.staff.has_perm(permissions.VIEW_DASHBOARD, self.course.id)
