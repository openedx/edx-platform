"""
Tests for the Course Outline view and supporting views.
"""
from django.conf import settings
from django.core.urlresolvers import reverse

from student.models import CourseEnrollment
from student.tests.factories import UserFactory

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls


class TestCourseOutlinePage(SharedModuleStoreTestCase):
    """
    Test the new course outline view.
    """
    @classmethod
    def setUpClass(cls):
        """Set up the simplest course possible."""
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(TestCourseOutlinePage, cls).setUpClassAndTestData():
            cls.course = CourseFactory.create()
            with cls.store.bulk_operations(cls.course.id):
                cls.chapter = ItemFactory.create(category='chapter', parent_location=cls.course.location)
                cls.section = ItemFactory.create(category='sequential', parent_location=cls.chapter.location)
                cls.vertical = ItemFactory.create(category='vertical', parent_location=cls.section.location)

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.password = 'test'
        cls.user = UserFactory(password=cls.password)
        CourseEnrollment.enroll(cls.user, cls.course.id)

    def setUp(self):
        self.client.login(username=self.user.username, password=self.password)

    def test_render(self):
        url = reverse(
            'unified_course_view',
            kwargs={
                'course_id': unicode(self.course.id),
            }
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response_content = response.content.decode("utf-8")
        self.assertIn(self.chapter.display_name, response_content)
        self.assertIn(self.section.display_name, response_content)
        self.assertNotIn(self.vertical.display_name, response_content)
