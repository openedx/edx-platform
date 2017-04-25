"""
Tests for the Course Outline view and supporting views.
"""
import datetime
import ddt
import json

from django.core.urlresolvers import reverse
from pyquery import PyQuery as pq

from courseware.tests.factories import StaffFactory
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.course_module import DEFAULT_START_DATE

from .test_course_home import course_home_url

TEST_PASSWORD = 'test'
FUTURE_DAY = datetime.datetime.now() + datetime.timedelta(days=30)
PAST_DAY = datetime.datetime.now() - datetime.timedelta(days=30)


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
                vertical = ItemFactory.create(category='vertical', parent_location=section.location)
            course.children = [chapter]
            chapter.children = [section]
            section.children = [vertical]
            cls.courses.append(course)

            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                section = ItemFactory.create(category='sequential', parent_location=chapter.location)
                section2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
                vertical = ItemFactory.create(category='vertical', parent_location=section.location)
                vertical2 = ItemFactory.create(category='vertical', parent_location=section2.location)
            course.children = [chapter]
            chapter.children = [section, section2]
            section.children = [vertical]
            section2.children = [vertical2]
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
                vertical = ItemFactory.create(category='vertical', parent_location=section.location)
            course.children = [chapter]
            chapter.children = [section]
            section.children = [vertical]
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

    def test_outline_details(self):
        for course in self.courses:

            url = course_home_url(course)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            response_content = response.content.decode("utf-8")

            self.assertTrue(course.children)
            for chapter in course.children:
                self.assertIn(chapter.display_name, response_content)
                self.assertTrue(chapter.children)
                for section in chapter.children:
                    self.assertIn(section.display_name, response_content)
                    if section.graded:
                        self.assertIn(section.due.strftime('%Y-%m-%d %H:%M:%S'), response_content)
                        self.assertIn(section.format, response_content)
                    self.assertTrue(section.children)
                    for vertical in section.children:
                        self.assertNotIn(vertical.display_name, response_content)

    def test_start_course(self):
        """
        Tests that the start course button appears when the course has never been accessed.

        Technically, this is a course home test, and not a course outline test, but checking the counts of
        start/resume course should be done together to not get a false positive.

        """
        course = self.courses[0]

        response = self.client.get(course_home_url(course))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Start Course', count=1)
        self.assertContains(response, 'Resume Course', count=0)

        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/course/' + course.url_name))

    def test_resume_course(self):
        """
        Tests that two resume course buttons appear when the course has been accessed.

        Technically, this is a mix of a course home and course outline test, but checking the counts of start/resume
        course should be done together to not get a false positive.

        """
        course = self.courses[0]

        # first navigate to a section to make it the last accessed
        chapter = course.children[0]
        section = chapter.children[0]
        last_accessed_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': course.id.to_deprecated_string(),
                'chapter': chapter.url_name,
                'section': section.url_name,
            }
        )
        self.assertEqual(200, self.client.get(last_accessed_url).status_code)

        # check resume course buttons
        response = self.client.get(course_home_url(course))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Start Course', count=0)
        self.assertContains(response, 'Resume Course', count=2)

        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/sequential/' + section.url_name))


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


@ddt.ddt
class TestEmptyCourseOutlinePage(SharedModuleStoreTestCase):
    """
    Test the new course outline view.
    """
    @ddt.data(
        (FUTURE_DAY, 'This course has not started yet, and will launch on'),
        (PAST_DAY, "We're still working on course content."),
        (DEFAULT_START_DATE, 'This course has not started yet.'),
    )
    @ddt.unpack
    def test_empty_course_rendering(self, start_date, expected_text):
        course = CourseFactory.create(start=start_date)
        test_user = UserFactory(password=TEST_PASSWORD)
        CourseEnrollment.enroll(test_user, course.id)
        self.client.login(username=test_user.username, password=TEST_PASSWORD)
        url = course_home_url(course)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_text)
