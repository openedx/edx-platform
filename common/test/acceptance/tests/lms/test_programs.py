"""Acceptance tests for LMS-hosted Programs pages"""
from nose.plugins.attrib import attr

from ...fixtures.programs import FakeProgram, ProgramsFixture, ProgramsConfigMixin
from ...fixtures.course import CourseFixture
from ..helpers import UniqueCourseTest
from ...pages.lms.auto_auth import AutoAuthPage
from ...pages.lms.programs import ProgramListingPage


class ProgramListingPageBase(ProgramsConfigMixin, UniqueCourseTest):
    """Base class used for program listing page tests."""
    def setUp(self):
        super(ProgramListingPageBase, self).setUp()

        self.set_programs_api_configuration(is_enabled=True)
        self.listing_page = ProgramListingPage(self.browser)

    def stub_api(self, course_id=None):
        """Stub out the programs API with fake data."""
        name = 'Fake Program'
        status = 'active'
        org_key = self.course_info['org']
        course_id = course_id if course_id else self.course_id

        ProgramsFixture().install_programs([
            FakeProgram(name=name, status=status, org_key=org_key, course_id=course_id),
        ])

    def auth(self, enroll=True):
        """Authenticate, enrolling the user in the configured course if requested."""
        CourseFixture(**self.course_info).install()

        course_id = self.course_id if enroll else None
        AutoAuthPage(self.browser, course_id=course_id).visit()


class ProgramListingPageTest(ProgramListingPageBase):
    """Verify user-facing behavior of the program listing page."""
    def test_no_enrollments(self):
        """Verify that no cards appear when the user has no enrollments."""
        self.stub_api()
        self.auth(enroll=False)
        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)

    def test_no_programs(self):
        """
        Verify that no cards appear when the user has enrollments
        but none are included in an active program.
        """
        course_id = self.course_id.replace(
            self.course_info['run'],
            'other_run'
        )
        self.stub_api(course_id=course_id)
        self.auth()
        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)

    def test_enrollments_and_programs(self):
        """
        Verify that cards appear when the user has enrollments
        which are included in at least one active program.
        """
        self.stub_api()
        self.auth()
        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertTrue(self.listing_page.are_cards_present)


@attr('a11y')
class ProgramListingPageA11yTest(ProgramListingPageBase):
    """Test program listing page accessibility."""

    def test_empty_a11y(self):
        """Test a11y of the page's empty state."""
        self.stub_api()
        self.auth(enroll=False)
        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)

        self.listing_page.a11y_audit.check_for_accessibility_errors()

    def test_cards_a11y(self):
        """Test a11y when program cards are present."""
        self.stub_api()
        self.auth()
        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertTrue(self.listing_page.are_cards_present)

        self.listing_page.a11y_audit.check_for_accessibility_errors()
