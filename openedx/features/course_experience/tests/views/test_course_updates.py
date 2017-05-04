"""
Tests for the course updates page.
"""
from django.core.urlresolvers import reverse

from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.html_module import CourseInfoModule
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

TEST_PASSWORD = 'test'


def course_updates_url(course):
    """
    Returns the URL for the course's home page
    """
    return reverse(
        'openedx.course_experience.course_updates',
        kwargs={
            'course_id': unicode(course.id),
        }
    )


class TestCourseUpdatesPage(SharedModuleStoreTestCase):
    """
    Test the course updates page.
    """
    @classmethod
    def setUpClass(cls):
        """Set up the simplest course possible."""
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(TestCourseUpdatesPage, cls).setUpClassAndTestData():
            with cls.store.default_store(ModuleStoreEnum.Type.split):
                cls.course = CourseFactory.create()
                with cls.store.bulk_operations(cls.course.id):
                    # Create a basic course structure
                    chapter = ItemFactory.create(category='chapter', parent_location=cls.course.location)
                    section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                    ItemFactory.create(category='vertical', parent_location=section.location)

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.user = UserFactory(password=TEST_PASSWORD)
        CourseEnrollment.enroll(cls.user, cls.course.id)

        # Create course updates
        cls.create_course_updates(cls.course, cls.user)

    @classmethod
    def create_course_updates(cls, course, user, count=5):
        """
        Create some test course updates.
        """
        updates_usage_key = course.id.make_usage_key('course_info', 'updates')
        course_updates = modulestore().create_item(
            user.id,
            updates_usage_key.course_key,
            updates_usage_key.block_type,
            block_id=updates_usage_key.block_id
        )
        course_updates.data = u'<ol><li><a href="test">Test Update</a></li></ol>'
        modulestore().update_item(course_updates, user.id)

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseUpdatesPage, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def test_view(self):
        url = course_updates_url(self.course)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode("utf-8")
        self.assertIn('<a href="test">Test Update</a>', response_content)

    def test_queries(self):
        # Fetch the view and verify that the query counts haven't changed
        with self.assertNumQueries(32):
            with check_mongo_calls(4):
                url = course_updates_url(self.course)
                self.client.get(url)
