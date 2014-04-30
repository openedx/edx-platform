"""
Acceptance tests for Studio related to the container page.
"""
from ..pages.studio.auto_auth import AutoAuthPage
from ..pages.studio.overview import CourseOutlinePage
from ..fixtures.course import CourseFixture, XBlockFixtureDesc

from .helpers import UniqueCourseTest


class ContainerBase(UniqueCourseTest):
    """
    Base class for tests that do operations on the container page.
    """
    __test__ = False

    def setUp(self):
        """
        Create a unique identifier for the course used in this test.
        """
        # Ensure that the superclass sets up
        super(ContainerBase, self).setUp()

        self.auth_page = AutoAuthPage(self.browser, staff=True)
        self.outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.setup_fixtures()

        self.auth_page.visit()

    def setup_fixtures(self):
        course_fix = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )

        course_fix.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc('vertical', 'Test Unit').add_children(
                        XBlockFixtureDesc('vertical', 'Test Container').add_children(
                            XBlockFixtureDesc('vertical', 'Group A').add_children(
                                XBlockFixtureDesc('html', 'Group A Item 1'),
                                XBlockFixtureDesc('html', 'Group A Item 2')
                            ),
                            XBlockFixtureDesc('vertical', 'Group B').add_children(
                                XBlockFixtureDesc('html', 'Group B Item 1'),
                                XBlockFixtureDesc('html', 'Group B Item 2')
                            )
                        )
                    )
                )
            )
        ).install()

    def go_to_container_page(self, make_draft=False):
        self.outline.visit()
        subsection = self.outline.section('Test Section').subsection('Test Subsection')
        unit = subsection.toggle_expand().unit('Test Unit').go_to()
        if make_draft:
            unit.edit_draft()
        container = unit.components[0].go_to_container()
        return container


class DragAndDropTest(ContainerBase):
    """
    Tests of reordering within the container page.
    """
    __test__ = True

    def verify_ordering(self, container, expected_ordering):
        xblocks = container.xblocks
        for xblock in xblocks:
            print xblock.name
        # TODO: need to verify parenting structure on page. Just checking
        # the order of the xblocks is not sufficient.


    def test_reorder_in_group(self):
        container = self.go_to_container_page(make_draft=True)
        # Swap Group A Item 1 and Group A Item 2.
        container.drag(1, 2)

        expected_ordering = [{"Group A": ["Group A Item 2", "Group A Item 1"]},
                             {"Group B": ["Group B Item 1", "Group B Item 2"]}]
        self.verify_ordering(container, expected_ordering)

        # Reload the page to see that the reordering was saved persisted.
        container = self.go_to_container_page()
        self.verify_ordering(container, expected_ordering)
