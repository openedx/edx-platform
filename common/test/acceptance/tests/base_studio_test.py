from ..pages.studio.auto_auth import AutoAuthPage
from ..fixtures.course import CourseFixture
from .helpers import UniqueCourseTest
from ..pages.studio.overview import CourseOutlinePage


class StudioCourseTest(UniqueCourseTest):
    """
    Base class for all Studio course tests.
    """

    def setUp(self):
        """
        Install a course with no content using a fixture.
        """
        super(StudioCourseTest, self).setUp()
        self.course_fixture = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )
        self.populate_course_fixture(self.course_fixture)
        self.course_fixture.install()
        self.user = self.course_fixture.user
        self.log_in(self.user)

    def populate_course_fixture(self, course_fixture):
        """
        Populate the children of the test course fixture.
        """
        pass

    def log_in(self, user, is_staff=False):
        """
        Log in as the user that created the course. The user will be given instructor access
        to the course and enrolled in it. By default the user will not have staff access unless
        is_staff is passed as True.
        """
        self.auth_page = AutoAuthPage(
            self.browser,
            staff=is_staff,
            username=user.get('username'),
            email=user.get('email'),
            password=user.get('password')
        )
        self.auth_page.visit()


class ContainerBase(StudioCourseTest):
    """
    Base class for tests that do operations on the container page.
    """

    def setUp(self):
        """
        Create a unique identifier for the course used in this test.
        """
        # Ensure that the superclass sets up
        super(ContainerBase, self).setUp()

        self.outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

    def go_to_nested_container_page(self):
        """
        Go to the nested container page.
        """
        unit = self.go_to_unit_page()
        # The 0th entry is the unit page itself.
        container = unit.xblocks[1].go_to_container()
        return container

    def go_to_unit_page(self, section_name='Test Section', subsection_name='Test Subsection', unit_name='Test Unit'):
        """
        Go to the test unit page.

        If make_draft is true, the unit page will be put into draft mode.
        """
        self.outline.visit()
        subsection = self.outline.section(section_name).subsection(subsection_name)
        return subsection.toggle_expand().unit(unit_name).go_to()

    def verify_ordering(self, container, expected_orderings):
        """
        Verifies the expected ordering of xblocks on the page.
        """
        xblocks = container.xblocks
        blocks_checked = set()
        for expected_ordering in expected_orderings:
            for xblock in xblocks:
                parent = expected_ordering.keys()[0]
                if xblock.name == parent:
                    blocks_checked.add(parent)
                    children = xblock.children
                    expected_length = len(expected_ordering.get(parent))
                    self.assertEqual(
                        expected_length, len(children),
                        "Number of children incorrect for group {0}. Expected {1} but got {2}.".format(parent, expected_length, len(children)))
                    for idx, expected in enumerate(expected_ordering.get(parent)):
                        self.assertEqual(expected, children[idx].name)
                        blocks_checked.add(expected)
                    break
        self.assertEqual(len(blocks_checked), len(xblocks))

    def do_action_and_verify(self, action, expected_ordering):
        """
        Perform the supplied action and then verify the resulting ordering.
        """
        container = self.go_to_nested_container_page()
        action(container)

        self.verify_ordering(container, expected_ordering)

        # Reload the page to see that the change was persisted.
        container = self.go_to_nested_container_page()
        self.verify_ordering(container, expected_ordering)
