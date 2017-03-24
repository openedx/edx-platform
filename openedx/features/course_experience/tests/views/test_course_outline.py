"""
Tests for the Course Outline view and supporting views.
"""
from mock import patch
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
                course.last_accessed = section.url_name

            cls.courses.append(course)

            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                section2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
                ItemFactory.create(category='vertical', parent_location=section.location)
                ItemFactory.create(category='vertical', parent_location=section2.location)
                course.last_accessed = None

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

    @patch('openedx.features.course_experience.views.course_outline.get_last_accessed_courseware')
    def test_render(self, patched_get_last_accessed):
        for course in self.courses:
            patched_get_last_accessed.return_value = (None, course.last_accessed)
            url = reverse(
                'edx.course_experience.course_home',
                kwargs={
                    'course_id': unicode(course.id),
                }
            )
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            response_content = response.content.decode("utf-8")

            if course.last_accessed is not None:
                self.assertIn('Resume Course', response_content)
            else:
                self.assertNotIn('Resume Course', response_content)
            for chapter in course.children:
                self.assertIn(chapter.display_name, response_content)
                for section in chapter.children:
                    self.assertIn(section.display_name, response_content)
                    for vertical in section.children:
                        self.assertNotIn(vertical.display_name, response_content)
