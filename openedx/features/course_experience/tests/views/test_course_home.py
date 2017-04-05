"""
Tests for the course home page.
"""
from django.core.urlresolvers import reverse

from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls

TEST_PASSWORD = 'test'


def course_home_url(course):
    """
    Returns the URL for the course's home page
    """
    return reverse(
        'edx.course_experience.course_home',
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
                cls.course = CourseFactory.create()
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

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseHomePage, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def test_queries(self):
        """
        Verify that the view's query count doesn't regress.
        """
        # Pre-fill the course blocks cache
        get_course_in_cache(self.course.id)

        # Fetch the view and verify the query counts
        with self.assertNumQueries(36):
            with check_mongo_calls(3):
                url = course_home_url(self.course)
                self.client.get(url)
