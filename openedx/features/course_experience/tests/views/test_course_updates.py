"""
Tests for the course updates page.
"""
from datetime import date

from courseware.courses import get_course_info_usage_key
from django.urls import reverse
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES, override_waffle_flag
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.course_experience.views.course_updates import STATUS_VISIBLE
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

TEST_PASSWORD = 'test'

QUERY_COUNT_TABLE_BLACKLIST = WAFFLE_TABLES


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


def create_course_update(course, user, content, date='December 31, 1999'):
    """
    Creates a test welcome message for the specified course.
    """
    updates_usage_key = get_course_info_usage_key(course, 'updates')
    try:
        course_updates = modulestore().get_item(updates_usage_key)
    except ItemNotFoundError:
        course_updates = create_course_updates_block(course, user)
    course_updates.items.append({
        "id": len(course_updates.items) + 1,
        "date": date,
        "content": content,
        "status": STATUS_VISIBLE
    })
    modulestore().update_item(course_updates, user.id)


def create_course_updates_block(course, user):
    """
    Create a course updates block.
    """
    updates_usage_key = get_course_info_usage_key(course, 'updates')
    course_updates = modulestore().create_item(
        user.id,
        updates_usage_key.course_key,
        updates_usage_key.block_type,
        block_id=updates_usage_key.block_id
    )
    course_updates.data = ''
    return course_updates


def remove_course_updates(user, course):
    """
    Remove any course updates in the specified course.
    """
    updates_usage_key = get_course_info_usage_key(course, 'updates')
    try:
        course_updates = modulestore().get_item(updates_usage_key)
        modulestore().delete_item(course_updates.location, user.id)
    except (ItemNotFoundError, ValueError):
        pass


class TestCourseUpdatesPage(SharedModuleStoreTestCase):
    """
    Test the course updates page.
    """
    @classmethod
    def setUpClass(cls):
        """Set up the simplest course possible."""
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

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseUpdatesPage, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def tearDown(self):
        remove_course_updates(self.user, self.course)
        super(TestCourseUpdatesPage, self).tearDown()

    def test_view(self):
        create_course_update(self.course, self.user, 'First Message')
        create_course_update(self.course, self.user, 'Second Message')
        url = course_updates_url(self.course)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'First Message')
        self.assertContains(response, 'Second Message')

    def test_queries(self):
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=date(2018, 1, 1))
        create_course_update(self.course, self.user, 'First Message')

        # Pre-fetch the view to populate any caches
        course_updates_url(self.course)

        # Fetch the view and verify that the query counts haven't changed
        with self.assertNumQueries(50, table_blacklist=QUERY_COUNT_TABLE_BLACKLIST):
            with check_mongo_calls(4):
                url = course_updates_url(self.course)
                self.client.get(url)
