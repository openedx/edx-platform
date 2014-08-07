from ..pages.studio.auto_auth import AutoAuthPage
from ..fixtures.course import CourseFixture
from .helpers import UniqueCourseTest



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
