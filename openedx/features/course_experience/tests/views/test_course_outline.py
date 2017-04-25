"""
Tests for the Course Outline view and supporting views.
"""
import datetime
from mock import patch
import json

from django.core.urlresolvers import reverse

from courseware.tests.factories import StaffFactory
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from .test_course_home import course_home_url

TEST_PASSWORD = 'test'


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

            cls.courses.append(course)

            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                section = ItemFactory.create(
                    category='sequential',
                    parent_location=chapter.location,
                    due=datetime.datetime.now(),
                    graded=True,
                    format='Homework',
                )
                ItemFactory.create(category='vertical', parent_location=section.location)
                course.last_accessed = section.url_name
            cls.courses.append(course)

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.user = UserFactory(password=TEST_PASSWORD)
        for course in cls.courses:
            CourseEnrollment.enroll(cls.user, course.id)

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseOutlinePage, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    @patch('openedx.features.course_experience.views.course_outline.get_last_accessed_courseware')
    def test_render(self, patched_get_last_accessed):
        for course in self.courses:
            patched_get_last_accessed.return_value = (None, course.last_accessed)
            url = course_home_url(course)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            response_content = response.content.decode("utf-8")

            self.assertIn('Resume Course', response_content)
            for chapter in course.children:
                self.assertIn(chapter.display_name, response_content)
                for section in chapter.children:
                    self.assertIn(section.display_name, response_content)
                    if section.graded:
                        self.assertIn(section.due, response_content)
                        self.assertIn(section.format, response_content)
                    for vertical in section.children:
                        self.assertNotIn(vertical.display_name, response_content)


class TestCourseOutlinePreview(SharedModuleStoreTestCase):
    """
    Unit tests for staff preview of the course outline.
    """
    def update_masquerade(self, course, role, group_id=None, user_name=None):
        """
        Toggle masquerade state.
        """
        masquerade_url = reverse(
            'masquerade_update',
            kwargs={
                'course_key_string': unicode(course.id),
            }
        )
        response = self.client.post(
            masquerade_url,
            json.dumps({'role': role, 'group_id': group_id, 'user_name': user_name}),
            'application/json'
        )
        self.assertEqual(response.status_code, 200)
        return response

    def test_preview(self):
        """
        Verify the behavior of preview for the course outline.
        """
        course = CourseFactory.create(
            start=datetime.datetime.now() - datetime.timedelta(days=30)
        )
        staff_user = StaffFactory(course_key=course.id, password=TEST_PASSWORD)
        CourseEnrollment.enroll(staff_user, course.id)

        future_date = datetime.datetime.now() + datetime.timedelta(days=30)
        with self.store.bulk_operations(course.id):
            chapter = ItemFactory.create(
                category='chapter',
                parent_location=course.location,
                display_name='First Chapter',
            )
            section = ItemFactory.create(category='sequential', parent_location=chapter.location)
            ItemFactory.create(category='vertical', parent_location=section.location)
            chapter = ItemFactory.create(
                category='chapter',
                parent_location=course.location,
                display_name='Future Chapter',
                due=future_date,
            )
            section = ItemFactory.create(category='sequential', parent_location=chapter.location)
            ItemFactory.create(category='vertical', parent_location=section.location)

        # Verify that a staff user sees a chapter with a due date in the future
        self.client.login(username=staff_user.username, password='test')
        url = course_home_url(course)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Future Chapter')

        # Verify that staff masquerading as a learner does not see the future chapter.
        self.update_masquerade(course, role='student')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Future Chapter')
