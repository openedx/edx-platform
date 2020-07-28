"""Acceptance tests for LMS-hosted Programs pages"""


from common.test.acceptance.fixtures.catalog import CatalogFixture, CatalogIntegrationMixin
from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.fixtures.programs import ProgramsConfigMixin
from common.test.acceptance.pages.common.auto_auth import AutoAuthPage
from common.test.acceptance.pages.lms.catalog import CacheProgramsPage
from common.test.acceptance.pages.lms.programs import ProgramDetailsPage, ProgramListingPage
from common.test.acceptance.tests.helpers import UniqueCourseTest
from openedx.core.djangoapps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    PathwayFactory,
    ProgramFactory,
    ProgramTypeFactory
)


class ProgramPageBase(ProgramsConfigMixin, CatalogIntegrationMixin, UniqueCourseTest):
    """Base class used for program listing page tests."""
    def setUp(self):
        super(ProgramPageBase, self).setUp()

        self.set_programs_api_configuration(is_enabled=True)

        self.programs = ProgramFactory.create_batch(3)
        self.pathways = PathwayFactory.create_batch(3)
        for pathway in self.pathways:
            self.programs += pathway['programs']

        # add some of the previously created programs to some pathways
        self.pathways[0]['programs'].extend([self.programs[0], self.programs[1]])
        self.pathways[1]['programs'].append(self.programs[0])

        self.username = None

    def auth(self, enroll=True):
        """Authenticate, enrolling the user in the configured course if requested."""
        CourseFixture(**self.course_info).install()

        course_id = self.course_id if enroll else None
        auth_page = AutoAuthPage(self.browser, course_id=course_id)
        auth_page.visit()

        self.username = auth_page.user_info['username']

    def create_program(self):
        """DRY helper for creating test program data."""
        course_run = CourseRunFactory(key=self.course_id)
        course = CourseFactory(course_runs=[course_run])

        program_type = ProgramTypeFactory()
        return ProgramFactory(courses=[course], type=program_type['name'])

    def stub_catalog_api(self, programs, pathways):
        """
        Stub the discovery service's program list and detail API endpoints, as well as
        the credit pathway list endpoint.
        """
        self.set_catalog_integration(is_enabled=True, service_username=self.username)
        CatalogFixture().install_programs(programs)

        program_types = [program['type'] for program in programs]
        CatalogFixture().install_program_types(program_types)

        CatalogFixture().install_pathways(pathways)

    def cache_programs(self):
        """
        Populate the LMS' cache of program data.
        """
        cache_programs_page = CacheProgramsPage(self.browser)
        cache_programs_page.visit()


class ProgramListingPageA11yTest(ProgramPageBase):
    """Test program listing page accessibility."""
    a11y = True

    def setUp(self):
        super(ProgramListingPageA11yTest, self).setUp()

        self.listing_page = ProgramListingPage(self.browser)

        self.program = self.create_program()

    def test_empty_a11y(self):
        """Test a11y of the page's empty state."""
        self.listing_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'region',  # TODO: AC-932
            ]
        })
        self.auth(enroll=False)
        self.stub_catalog_api(programs=[self.program], pathways=[])
        self.cache_programs()

        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertFalse(self.listing_page.are_cards_present)
        self.listing_page.a11y_audit.check_for_accessibility_errors()

    def test_cards_a11y(self):
        """Test a11y when program cards are present."""
        self.listing_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'landmark-complementary-is-top-level',  # TODO: AC-939
                'region',  # TODO: AC-932
            ]
        })
        self.auth()
        self.stub_catalog_api(programs=[self.program], pathways=[])
        self.cache_programs()

        self.listing_page.visit()

        self.assertTrue(self.listing_page.is_sidebar_present)
        self.assertTrue(self.listing_page.are_cards_present)
        self.listing_page.a11y_audit.check_for_accessibility_errors()


class ProgramDetailsPageA11yTest(ProgramPageBase):
    """Test program details page accessibility."""
    a11y = True

    def setUp(self):
        super(ProgramDetailsPageA11yTest, self).setUp()

        self.details_page = ProgramDetailsPage(self.browser)

        self.program = self.create_program()
        self.program['uuid'] = self.details_page.program_uuid

    def test_a11y(self):
        """Test the page's a11y compliance."""
        self.details_page.a11y_audit.config.set_rules({
            "ignore": [
                'aria-valid-attr',  # TODO: LEARNER-6611 & LEARNER-6865
                'landmark-complementary-is-top-level',  # TODO: AC-939
                'region',  # TODO: AC-932
            ]
        })
        self.auth()
        self.stub_catalog_api(programs=[self.program], pathways=[])
        self.cache_programs()

        self.details_page.visit()

        self.details_page.a11y_audit.check_for_accessibility_errors()
