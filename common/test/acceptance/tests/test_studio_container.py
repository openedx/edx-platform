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

        self.container_title = ""
        self.group_a = "Expand or Collapse\nGroup A"
        self.group_b = "Expand or Collapse\nGroup B"
        self.group_empty = "Expand or Collapse\nGroup Empty"
        self.group_a_item_1 = "Group A Item 1"
        self.group_a_item_2 = "Group A Item 2"
        self.group_b_item_1 = "Group B Item 1"
        self.group_b_item_2 = "Group B Item 2"

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
                                XBlockFixtureDesc('html', self.group_a_item_1),
                                XBlockFixtureDesc('html', self.group_a_item_2)
                            ),
                            XBlockFixtureDesc('vertical', 'Group Empty'),
                            XBlockFixtureDesc('vertical', 'Group B').add_children(
                                XBlockFixtureDesc('html', self.group_b_item_1),
                                XBlockFixtureDesc('html', self.group_b_item_2)
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

    def verify_ordering(self, container, expected_orderings):
        xblocks = container.xblocks
        for expected_ordering in expected_orderings:
            for xblock in xblocks:
                parent = expected_ordering.keys()[0]
                if xblock.name == parent:
                    children = xblock.children
                    expected_length = len(expected_ordering.get(parent))
                    self.assertEqual(
                        expected_length, len(children),
                        "Number of children incorrect for group {0}. Expected {1} but got {2}.".format(parent, expected_length, len(children)))
                    for idx, expected in enumerate(expected_ordering.get(parent)):
                        self.assertEqual(expected, children[idx].name)

    def drag_and_verify(self, source, target, expected_ordering, after=True):
        container = self.go_to_container_page(make_draft=True)
        container.drag(source, target, after)

        self.verify_ordering(container, expected_ordering)

        # Reload the page to see that the reordering was saved persisted.
        container = self.go_to_container_page()
        self.verify_ordering(container, expected_ordering)

    def test_reorder_in_group(self):
        """
        Drag Group B Item 2 before Group B Item 1.
        """
        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_1, self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_2, self.group_b_item_1]},
                             {self.group_empty: []}]
        self.drag_and_verify(6, 4, expected_ordering)

    def test_drag_to_top(self):
        """
        Drag Group A Item 1 to top level (outside of Group A).
        """
        expected_ordering = [{self.container_title: [self.group_a_item_1, self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]
        self.drag_and_verify(1, 0, expected_ordering, False)

    def test_drag_into_different_group(self):
        """
        Drag Group A Item 1 into Group B (last element).
        """
        expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
                             {self.group_a: [self.group_a_item_2]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2, self.group_a_item_1]},
                             {self.group_empty: []}]
        self.drag_and_verify(1, 6, expected_ordering)

    def test_drag_group_into_group(self):
        """
        Drag Group B into Group A (last element).
        """
        expected_ordering = [{self.container_title: [self.group_a, self.group_empty]},
                             {self.group_a: [self.group_a_item_1, self.group_a_item_2, self.group_b]},
                             {self.group_b: [self.group_b_item_1, self.group_b_item_2]},
                             {self.group_empty: []}]
        self.drag_and_verify(4, 2, expected_ordering)

    # Not able to drag into the empty group with automation (difficult even outside of automation).
    # def test_drag_into_empty(self):
    #     """
    #     Drag Group B Item 1 to Group Empty.
    #     """
    #     expected_ordering = [{self.container_title: [self.group_a, self.group_empty, self.group_b]},
    #                          {self.group_a: [self.group_a_item_1, self.group_a_item_2]},
    #                          {self.group_b: [self.group_b_item_2]},
    #                          {self.group_empty: [self.group_b_item_1]}]
    #     self.drag_and_verify(6, 4, expected_ordering, False)
