# -*- coding: utf-8 -*-
"""
End-to-end tests for the LMS Instructor Dashboard.
"""


import ddt

from common.test.acceptance.fixtures.certificates import CertificateConfigFixture
from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.dashboard import DashboardPage
from common.test.acceptance.pages.lms.instructor_dashboard import (
    InstructorDashboardPage,
)
from common.test.acceptance.tests.helpers import (
    EventsTestMixin,
    UniqueCourseTest,
    disable_animations,
)
from openedx.core.lib.tests import attr


class BaseInstructorDashboardTest(EventsTestMixin, UniqueCourseTest):
    """
    Mixin class for testing the instructor dashboard.
    """
    def log_in_as_instructor(self, global_staff=True, course_access_roles=None):
        """
        Login with an instructor account.

        Args:
            course_access_roles (str[]): List of course access roles that should be assigned to the user.

        Returns
            username (str)
            user_id (int)
        """
        course_access_roles = course_access_roles or []
        auto_auth_page = AutoAuthPage(
            self.browser, course_id=self.course_id, staff=global_staff, course_access_roles=course_access_roles
        )
        auto_auth_page.visit()
        user_info = auto_auth_page.user_info
        return user_info['username'], user_info['user_id'], user_info['email'], user_info['password']

    def visit_instructor_dashboard(self):
        """
        Visits the instructor dashboard.
        """
        instructor_dashboard_page = InstructorDashboardPage(self.browser, self.course_id)
        instructor_dashboard_page.visit()
        return instructor_dashboard_page


@attr('a11y')
class LMSInstructorDashboardA11yTest(BaseInstructorDashboardTest):
    """
    Instructor dashboard base accessibility test.
    """
    def setUp(self):
        super(LMSInstructorDashboardA11yTest, self).setUp()
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.log_in_as_instructor()
        self.instructor_dashboard_page = self.visit_instructor_dashboard()

    def test_instructor_dashboard_a11y(self):
        self.instructor_dashboard_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        self.instructor_dashboard_page.a11y_audit.check_for_accessibility_errors()


@ddt.ddt
class BulkEmailTest(BaseInstructorDashboardTest):
    """
    End-to-end tests for bulk emailing from instructor dash.
    """
    shard = 23

    def setUp(self):
        super(BulkEmailTest, self).setUp()
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.log_in_as_instructor()
        instructor_dashboard_page = self.visit_instructor_dashboard()
        self.send_email_page = instructor_dashboard_page.select_bulk_email()

    @attr('a11y')
    def test_bulk_email_a11y(self):
        """
        Bulk email accessibility tests
        """
        self.send_email_page.a11y_audit.config.set_scope([
            '#section-send-email'
        ])
        self.send_email_page.a11y_audit.config.set_rules({
            "ignore": [
                'button-name',  # TODO: TNL-5830
                'aria-allowed-role',  # TODO: AC-936
                'color-contrast',  # TODO: AC-938
                'listitem'  # TODO: AC-937
            ]
        })
        self.send_email_page.a11y_audit.check_for_accessibility_errors()


@attr(shard=20)
class AutoEnrollmentWithCSVTest(BaseInstructorDashboardTest):
    """
    End-to-end tests for Auto-Registration and enrollment functionality via CSV file.
    """

    def setUp(self):
        super(AutoEnrollmentWithCSVTest, self).setUp()
        self.course_fixture = CourseFixture(**self.course_info).install()
        self.log_in_as_instructor()
        instructor_dashboard_page = self.visit_instructor_dashboard()
        self.auto_enroll_section = instructor_dashboard_page.select_membership().select_auto_enroll_section()
        # Initialize the page objects
        self.dashboard_page = DashboardPage(self.browser)

    @attr('a11y')
    def test_auto_enroll_csv_a11y(self):
        """
        Auto-enrollment with CSV accessibility tests
        """
        self.auto_enroll_section.a11y_audit.config.set_scope([
            '#membership-list-widget-tpl'
        ])
        self.auto_enroll_section.a11y_audit.check_for_accessibility_errors()


@attr(shard=10)
@ddt.ddt
class CertificatesTest(BaseInstructorDashboardTest):
    """
    Tests for Certificates functionality on instructor dashboard.
    """

    def setUp(self):
        super(CertificatesTest, self).setUp()
        self.test_certificate_config = {
            'id': 1,
            'name': 'Certificate name',
            'description': 'Certificate description',
            'course_title': 'Course title override',
            'signatories': [],
            'version': 1,
            'is_active': True
        }
        CourseFixture(**self.course_info).install()
        self.cert_fixture = CertificateConfigFixture(self.course_id, self.test_certificate_config)
        self.cert_fixture.install()
        self.user_name, self.user_id, __, __ = self.log_in_as_instructor()
        self.instructor_dashboard_page = self.visit_instructor_dashboard()
        self.certificates_section = self.instructor_dashboard_page.select_certificates()
        disable_animations(self.certificates_section)

    @attr('a11y')
    def test_certificates_a11y(self):
        """
        Certificates page accessibility tests
        """
        self.certificates_section.a11y_audit.config.set_rules({
            "ignore": [
                'aria-hidden-focus'  # TODO: AC-938
            ]
        })
        self.certificates_section.a11y_audit.config.set_scope([
            '.certificates-wrapper'
        ])
        self.certificates_section.a11y_audit.check_for_accessibility_errors()


@attr(shard=20)
class CertificateInvalidationTest(BaseInstructorDashboardTest):
    """
    Tests for Certificates functionality on instructor dashboard.
    """

    @classmethod
    def setUpClass(cls):
        super(CertificateInvalidationTest, cls).setUpClass()

        # Create course fixture once each test run
        CourseFixture(
            org='test_org',
            number='335535897951379478207964576572017930000',
            run='test_run',
            display_name='Test Course 335535897951379478207964576572017930000',
        ).install()

    def setUp(self):
        super(CertificateInvalidationTest, self).setUp()
        # set same course number as we have in fixture json
        self.course_info['number'] = "335535897951379478207964576572017930000"

        # we have created a user with this id in fixture, and created a generated certificate for it.
        self.student_id = "99"
        self.student_name = "testcert"
        self.student_email = "cert@example.com"

        # Enroll above test user in the course
        AutoAuthPage(
            self.browser,
            username=self.student_name,
            email=self.student_email,
            course_id=self.course_id,
        ).visit()

        self.test_certificate_config = {
            'id': 1,
            'name': 'Certificate name',
            'description': 'Certificate description',
            'course_title': 'Course title override',
            'signatories': [],
            'version': 1,
            'is_active': True
        }

        self.cert_fixture = CertificateConfigFixture(self.course_id, self.test_certificate_config)
        self.cert_fixture.install()
        self.user_name, self.user_id, __, __ = self.log_in_as_instructor()
        self.instructor_dashboard_page = self.visit_instructor_dashboard()
        self.certificates_section = self.instructor_dashboard_page.select_certificates()

        disable_animations(self.certificates_section)

    @attr('a11y')
    def test_invalidate_certificates_a11y(self):
        """
        Certificate invalidation accessibility tests
        """
        self.certificates_section.a11y_audit.config.set_rules({
            "ignore": [
                'aria-hidden-focus'  # TODO: AC-938
            ]
        })
        self.certificates_section.a11y_audit.config.set_scope([
            '.certificates-wrapper'
        ])
        self.certificates_section.a11y_audit.check_for_accessibility_errors()
