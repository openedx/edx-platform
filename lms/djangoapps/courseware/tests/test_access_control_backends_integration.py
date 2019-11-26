# -*- coding: utf-8 -*-
"""
Integration tests for the access control framework with the Access Control Backends plugins.
"""
import datetime

import ddt
import pytz
from mock import patch, Mock
from opaque_keys.edx.locator import CourseLocator

import courseware.access as access
from lms.lib.access_control_backends import access_control_backends
from student.tests.factories import CourseEnrollmentAllowedFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@ddt.ddt
class AccessWithACLBackendsTestCase(ModuleStoreTestCase):
    """
    Integration tests for `access._has_access_course`.
    """

    def setUp(self):
        """
        Set up tests environment.
        """
        tomorrow = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1)
        self.user = UserFactory.create()
        self.course = Mock(
            enrollment_domain='',
            enrollment_end=tomorrow,
            enrollment_start=tomorrow,
            id=CourseLocator('edX', 'test', '2012_Fall'),
        )
        CourseEnrollmentAllowedFactory(email=self.user.email, course_id=self.course.id)

    def test_has_access_with_no_acl_backends(self):
        """
        Ensure that the `access._has_access_course` queries the Access Control Backends.
        """
        assert access._has_access_course(self.user, 'enroll', self.course)

    @ddt.data(False, True)
    def test_has_access_with_acl_backends(self, backend_access):
        """
        Ensure that the `access._has_access_course` queries the Access Control Backends.
        """
        with patch.object(access_control_backends, 'query', Mock(return_value=backend_access)):
            assert backend_access == access._has_access_course(self.user, 'enroll', self.course)
