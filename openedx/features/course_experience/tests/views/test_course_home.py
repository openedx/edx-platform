"""
Tests for the course home page.
"""
import ddt

from courseware.tests.factories import StaffFactory
from django.core.urlresolvers import reverse
from django.utils.http import urlquote_plus
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES, override_waffle_flag
from openedx.features.course_experience import SHOW_REVIEWS_TOOL_FLAG, UNIFIED_COURSE_TAB_FLAG
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import CourseUserType, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

from .helpers import add_course_mode
from .test_course_updates import create_course_update

TEST_PASSWORD = 'test'
TEST_CHAPTER_NAME = 'Test Chapter'
TEST_WELCOME_MESSAGE = '<h2>Welcome!</h2>'
TEST_UPDATE_MESSAGE = '<h2>Test Update!</h2>'
TEST_COURSE_UPDATES_TOOL = '/course/updates">'

QUERY_COUNT_TABLE_BLACKLIST = WAFFLE_TABLES


def course_home_url(course):
    """
    Returns the URL for the course's home page
    """
    return reverse(
        'openedx.course_experience.course_home',
        kwargs={
            'course_id': unicode(course.id),
        }
    )


class CourseHomePageTestCase(SharedModuleStoreTestCase):
    """
    Base class for testing the course home page.
    """
    @classmethod
    def setUpClass(cls):
        """
        Set up a course to be used for testing.
        """
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(CourseHomePageTestCase, cls).setUpClassAndTestData():
            with cls.store.default_store(ModuleStoreEnum.Type.split):
                cls.course = CourseFactory.create(org='edX', number='test', display_name='Test Course')
                with cls.store.bulk_operations(cls.course.id):
                    chapter = ItemFactory.create(
                        category='chapter',
                        parent_location=cls.course.location,
                        display_name=TEST_CHAPTER_NAME,
                    )
                    section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                    section2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
                    ItemFactory.create(category='vertical', parent_location=section.location)
                    ItemFactory.create(category='vertical', parent_location=section2.location)

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.staff_user = StaffFactory(course_key=cls.course.id, password=TEST_PASSWORD)
        cls.user = UserFactory(password=TEST_PASSWORD)
        CourseEnrollment.enroll(cls.user, cls.course.id)


class TestCourseHomePage(CourseHomePageTestCase):
    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseHomePage, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
    def test_welcome_message_when_unified(self):
        # Create a welcome message
        create_course_update(self.course, self.user, TEST_WELCOME_MESSAGE)

        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertContains(response, TEST_WELCOME_MESSAGE, status_code=200)

    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
    def test_welcome_message_when_not_unified(self):
        # Create a welcome message
        create_course_update(self.course, self.user, TEST_WELCOME_MESSAGE)

        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertNotContains(response, TEST_WELCOME_MESSAGE, status_code=200)

    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
    def test_updates_tool_visibility(self):
        """
        Verify that the updates course tool is visible only when the course
        has one or more updates.
        """
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertNotContains(response, TEST_COURSE_UPDATES_TOOL, status_code=200)

        create_course_update(self.course, self.user, TEST_UPDATE_MESSAGE)
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertContains(response, TEST_COURSE_UPDATES_TOOL, status_code=200)

    def test_queries(self):
        """
        Verify that the view's query count doesn't regress.
        """
        # Pre-fetch the view to populate any caches
        course_home_url(self.course)

        # Fetch the view and verify the query counts
        with self.assertNumQueries(39, table_blacklist=QUERY_COUNT_TABLE_BLACKLIST):
            with check_mongo_calls(4):
                url = course_home_url(self.course)
                self.client.get(url)


@ddt.ddt
class TestCourseHomePageAccess(CourseHomePageTestCase):
    """
    Test access to the course home page.
    """

    def setUp(self):
        super(TestCourseHomePageAccess, self).setUp()

        # Make this a verified course so that an upgrade message might be shown
        add_course_mode(self.course, upgrade_deadline_expired=False)

        # Add a welcome message
        create_course_update(self.course, self.staff_user, TEST_WELCOME_MESSAGE)

    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
    @override_waffle_flag(SHOW_REVIEWS_TOOL_FLAG, active=True)
    @ddt.data(
        CourseUserType.ANONYMOUS,
        CourseUserType.ENROLLED,
        CourseUserType.UNENROLLED,
        CourseUserType.UNENROLLED_STAFF,
    )
    def test_home_page(self, user_type):
        self.user = self.create_user_for_course(self.course, user_type)

        # Render the course home page
        url = course_home_url(self.course)
        response = self.client.get(url)

        # Verify that the course tools and dates are always shown
        self.assertContains(response, 'Course Tools')
        self.assertContains(response, 'Today is')

        # Verify that the outline, start button, course sock, and welcome message
        # are only shown to enrolled users.
        is_enrolled = user_type is CourseUserType.ENROLLED
        is_unenrolled_staff = user_type is CourseUserType.UNENROLLED_STAFF
        expected_count = 1 if (is_enrolled or is_unenrolled_staff) else 0
        self.assertContains(response, TEST_CHAPTER_NAME, count=expected_count)
        self.assertContains(response, 'Start Course', count=expected_count)
        self.assertContains(response, 'Learn About Verified Certificate', count=expected_count)
        self.assertContains(response, TEST_WELCOME_MESSAGE, count=expected_count)

    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
    @override_waffle_flag(SHOW_REVIEWS_TOOL_FLAG, active=True)
    @ddt.data(
        CourseUserType.ANONYMOUS,
        CourseUserType.ENROLLED,
        CourseUserType.UNENROLLED,
        CourseUserType.UNENROLLED_STAFF,
    )
    def test_home_page_not_unified(self, user_type):
        """
        Verifies the course home tab when not unified.
        """
        self.user = self.create_user_for_course(self.course, user_type)

        # Render the course home page
        url = course_home_url(self.course)
        response = self.client.get(url)

        # Verify that the course tools and dates are always shown
        self.assertContains(response, 'Course Tools')
        self.assertContains(response, 'Today is')

        # Verify that welcome messages are never shown
        self.assertNotContains(response, TEST_WELCOME_MESSAGE)

        # Verify that the outline, start button, course sock, and welcome message
        # are only shown to enrolled users.
        is_enrolled = user_type is CourseUserType.ENROLLED
        is_unenrolled_staff = user_type is CourseUserType.UNENROLLED_STAFF
        expected_count = 1 if (is_enrolled or is_unenrolled_staff) else 0
        self.assertContains(response, TEST_CHAPTER_NAME, count=expected_count)
        self.assertContains(response, 'Start Course', count=expected_count)
        self.assertContains(response, 'Learn About Verified Certificate', count=expected_count)

    def test_sign_in_button(self):
        """
        Verify that the sign in button will return to this page.
        """
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertContains(response, '/login?next={url}'.format(url=urlquote_plus(url)))
