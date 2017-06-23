"""
Tests for the course home page.
"""

from django.core.urlresolvers import reverse

from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.features.course_experience import UNIFIED_COURSE_TAB_FLAG
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

from .test_course_updates import create_course_update, remove_course_updates

TEST_PASSWORD = 'test'
TEST_WELCOME_MESSAGE = '<h2>Welcome!</h2>'


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


class TestCourseHomePage(SharedModuleStoreTestCase):
    """
    Test the course home page.
    """
    @classmethod
    def setUpClass(cls):
        """Set up the simplest course possible."""
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(TestCourseHomePage, cls).setUpClassAndTestData():
            with cls.store.default_store(ModuleStoreEnum.Type.split):
                cls.course = CourseFactory.create(org='edX', number='test', display_name='Test Course')
                with cls.store.bulk_operations(cls.course.id):
                    chapter = ItemFactory.create(category='chapter', parent_location=cls.course.location)
                    section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                    section2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
                    ItemFactory.create(category='vertical', parent_location=section.location)
                    ItemFactory.create(category='vertical', parent_location=section2.location)

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.user = UserFactory(password=TEST_PASSWORD)
        CourseEnrollment.enroll(cls.user, cls.course.id)

        # Create a welcome message
        create_course_update(cls.course, cls.user, TEST_WELCOME_MESSAGE)

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseHomePage, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def tearDown(self):
        remove_course_updates(self.course)
        super(TestCourseHomePage, self).tearDown()

    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=True)
    def test_welcome_message_when_unified(self):
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertContains(response, TEST_WELCOME_MESSAGE, status_code=200)

    @override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
    def test_welcome_message_when_not_unified(self):
        url = course_home_url(self.course)
        response = self.client.get(url)
        self.assertNotContains(response, TEST_WELCOME_MESSAGE, status_code=200)

    def test_queries(self):
        """
        Verify that the view's query count doesn't regress.
        """
        # Pre-fetch the view to populate any caches
        course_home_url(self.course)

        # Fetch the view and verify the query counts
        with self.assertNumQueries(49):
            with check_mongo_calls(5):
                url = course_home_url(self.course)
                self.client.get(url)
