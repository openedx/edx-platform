"""
Base classes used by studio tests.
"""
from bok_choy.web_app_test import WebAppTest
from ...pages.studio.auto_auth import AutoAuthPage
from ...fixtures.course import CourseFixture
from ...fixtures.library import LibraryFixture
from ..helpers import UniqueCourseTest
from ...pages.studio.overview import CourseOutlinePage
from ...pages.studio.utils import verify_ordering


class StudioCourseTest(UniqueCourseTest):
    """
    Base class for all Studio course tests.
    """

    def setUp(self, is_staff=False):
        """
        Install a course with no content using a fixture.
        """
        super(StudioCourseTest, self).setUp()
        self.install_course_fixture(is_staff)

    def install_course_fixture(self, is_staff=False):
        """
        Install a course fixture
        """
        self.course_fixture = CourseFixture(
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run'],
            self.course_info['display_name']
        )
        self.populate_course_fixture(self.course_fixture)
        self.course_fixture.install()
        self.user = self.course_fixture.user
        self.log_in(self.user, is_staff)

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

        Args:
            user(dict): dictionary containing user data: {'username': ..., 'email': ..., 'password': ...}
            is_staff(bool): register this user as staff
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

    def setUp(self, is_staff=False):
        """
        Create a unique identifier for the course used in this test.
        """
        # Ensure that the superclass sets up
        super(ContainerBase, self).setUp(is_staff=is_staff)

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
        return subsection.expand_subsection().unit(unit_name).go_to()

    def do_action_and_verify(self, action, expected_ordering):
        """
        Perform the supplied action and then verify the resulting ordering.
        """
        container = self.go_to_nested_container_page()
        action(container)

        verify_ordering(self, container, expected_ordering)

        # Reload the page to see that the change was persisted.
        container = self.go_to_nested_container_page()
        verify_ordering(self, container, expected_ordering)


class StudioLibraryTest(WebAppTest):
    """
    Base class for all Studio library tests.
    """
    as_staff = True

    def setUp(self):
        """
        Install a library with no content using a fixture.
        """
        super(StudioLibraryTest, self).setUp()
        fixture = LibraryFixture(
            'test_org',
            self.unique_id,
            'Test Library {}'.format(self.unique_id),
        )
        self.populate_library_fixture(fixture)
        fixture.install()
        self.library_fixture = fixture
        self.library_info = fixture.library_info
        self.library_key = fixture.library_key
        self.user = fixture.user
        self.log_in(self.user, self.as_staff)

    def populate_library_fixture(self, library_fixture):
        """
        Populate the children of the test course fixture.
        """
        pass

    def log_in(self, user, is_staff=False):
        """
        Log in as the user that created the library.
        By default the user will not have staff access unless is_staff is passed as True.
        """
        auth_page = AutoAuthPage(
            self.browser,
            staff=is_staff,
            username=user.get('username'),
            email=user.get('email'),
            password=user.get('password')
        )
        auth_page.visit()
