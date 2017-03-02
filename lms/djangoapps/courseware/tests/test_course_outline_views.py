"""
Tests for the Course Outline view and supporting views.
"""
from django.core.urlresolvers import reverse

from student.models import CourseEnrollment
from student.tests.factories import UserFactory

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


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
            cls.courses = []
            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                ItemFactory.create(category='vertical', parent_location=section.location)

            cls.courses.append(course)

            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                section2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
                ItemFactory.create(category='vertical', parent_location=section.location)
                ItemFactory.create(category='vertical', parent_location=section2.location)

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.password = 'test'
        cls.user = UserFactory(password=cls.password)
        for course in cls.courses:
            CourseEnrollment.enroll(cls.user, course.id)

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseOutlinePage, self).setUp()
        self.client.login(username=self.user.username, password=self.password)

    def test_render(self):
        for course in self.courses:
            url = reverse(
                'unified_course_view',
                kwargs={
                    'course_id': unicode(course.id),
                }
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            response_content = response.content.decode("utf-8")

            for chapter in course.children:
                self.assertIn(chapter.display_name, response_content)
                for section in chapter.children:
                    self.assertIn(section.display_name, response_content)
                    for vertical in section.children:
                        self.assertNotIn(vertical.display_name, response_content)
