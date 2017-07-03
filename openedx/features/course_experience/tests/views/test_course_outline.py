"""
Tests for the Course Outline view and supporting views.
"""
import datetime
import ddt
import json
from markupsafe import escape

from django.core.urlresolvers import reverse
from pyquery import PyQuery as pq

from courseware.tests.factories import StaffFactory
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.course_module import DEFAULT_START_DATE

from .test_course_home import course_home_url

TEST_PASSWORD = 'test'
FUTURE_DAY = datetime.datetime.now() + datetime.timedelta(days=30)
PAST_DAY = datetime.datetime.now() - datetime.timedelta(days=30)


class TestCourseOutlinePage(SharedModuleStoreTestCase):
    """
    Test the course outline view.
    """
    @classmethod
    def setUpClass(cls):
        """
        Set up an array of various courses to be tested.
        """
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(TestCourseOutlinePage, cls).setUpClassAndTestData():
            cls.courses = []
            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
                vertical = ItemFactory.create(category='vertical', parent_location=sequential.location)
            course.children = [chapter]
            chapter.children = [sequential]
            sequential.children = [vertical]
            cls.courses.append(course)

            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
                sequential2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
                vertical = ItemFactory.create(category='vertical', parent_location=sequential.location)
                vertical2 = ItemFactory.create(category='vertical', parent_location=sequential2.location)
            course.children = [chapter]
            chapter.children = [sequential, sequential2]
            sequential.children = [vertical]
            sequential2.children = [vertical2]
            cls.courses.append(course)

            course = CourseFactory.create()
            with cls.store.bulk_operations(course.id):
                chapter = ItemFactory.create(category='chapter', parent_location=course.location)
                sequential = ItemFactory.create(
                    category='sequential',
                    parent_location=chapter.location,
                    due=datetime.datetime.now(),
                    graded=True,
                    format='Homework',
                )
                vertical = ItemFactory.create(category='vertical', parent_location=sequential.location)
            course.children = [chapter]
            chapter.children = [sequential]
            sequential.children = [vertical]
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
                for sequential in chapter.children:
                    self.assertIn(sequential.display_name, response_content)
                    if sequential.graded:
                        self.assertIn(sequential.due.strftime('%Y-%m-%d %H:%M:%S'), response_content)
                        self.assertIn(sequential.format, response_content)
                    self.assertTrue(sequential.children)
                    for vertical in sequential.children:
                        self.assertNotIn(vertical.display_name, response_content)


class TestCourseOutlineResumeCourse(SharedModuleStoreTestCase):
    """
    Test start course and resume course for the course outline view.

    Technically, this mixes course home and course outline tests, but checking
    the counts of start/resume course should be done together to avoid false
    positives.

    """
    @classmethod
    def setUpClass(cls):
        """
        Creates a test course that can be used for non-destructive tests
        """
        # setUpClassAndTestData() already calls setUpClass on SharedModuleStoreTestCase
        # pylint: disable=super-method-not-called
        with super(TestCourseOutlineResumeCourse, cls).setUpClassAndTestData():
            cls.course = cls.create_test_course()

    @classmethod
    def setUpTestData(cls):
        """Set up and enroll our fake user in the course."""
        cls.user = UserFactory(password=TEST_PASSWORD)
        CourseEnrollment.enroll(cls.user, cls.course.id)

    @classmethod
    def create_test_course(cls):
        """
        Creates a test course.
        """
        course = CourseFactory.create()
        with cls.store.bulk_operations(course.id):
            chapter = ItemFactory.create(category='chapter', parent_location=course.location)
            sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
            sequential2 = ItemFactory.create(category='sequential', parent_location=chapter.location)
            vertical = ItemFactory.create(category='vertical', parent_location=sequential.location)
            vertical2 = ItemFactory.create(category='vertical', parent_location=sequential2.location)
        course.children = [chapter]
        chapter.children = [sequential, sequential2]
        sequential.children = [vertical]
        sequential2.children = [vertical2]
        if hasattr(cls, 'user'):
            CourseEnrollment.enroll(cls.user, course.id)
        return course

    def setUp(self):
        """
        Set up for the tests.
        """
        super(TestCourseOutlineResumeCourse, self).setUp()
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    def visit_sequential(self, course, chapter, sequential):
        """
        Navigates to the provided sequential.
        """
        last_accessed_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': course.id.to_deprecated_string(),
                'chapter': chapter.url_name,
                'section': sequential.url_name,
            }
        )
        self.assertEqual(200, self.client.get(last_accessed_url).status_code)

    def test_start_course(self):
        """
        Tests that the start course button appears when the course has never been accessed.

        Technically, this is a course home test, and not a course outline test, but checking the counts of
        start/resume course should be done together to not get a false positive.

        """
        course = self.course

        response = self.client.get(course_home_url(course))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Start Course', count=1)
        self.assertContains(response, 'Resume Course', count=0)

        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/course/' + course.url_name))

    def test_resume_course(self):
        """
        Tests that two resume course buttons appear when the course has been accessed.
        """
        course = self.course

        # first navigate to a sequential to make it the last accessed
        chapter = course.children[0]
        sequential = chapter.children[0]
        self.visit_sequential(course, chapter, sequential)

        # check resume course buttons
        response = self.client.get(course_home_url(course))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Start Course', count=0)
        self.assertContains(response, 'Resume Course', count=2)

        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/sequential/' + sequential.url_name))

    def test_resume_course_deleted_sequential(self):
        """
        Tests resume course when the last accessed sequential is deleted and
        there is another sequential in the vertical.

        """
        course = self.create_test_course()

        # first navigate to a sequential to make it the last accessed
        chapter = course.children[0]
        self.assertGreaterEqual(len(chapter.children), 2)
        sequential = chapter.children[0]
        sequential2 = chapter.children[1]
        self.visit_sequential(course, chapter, sequential)

        # remove one of the sequentials from the chapter
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
            self.store.delete_item(sequential.location, self.user.id)  # pylint: disable=no-member

        # check resume course buttons
        response = self.client.get(course_home_url(course))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Start Course', count=0)
        self.assertContains(response, 'Resume Course', count=2)

        content = pq(response.content)
        self.assertTrue(content('.action-resume-course').attr('href').endswith('/sequential/' + sequential2.url_name))

    def test_resume_course_deleted_sequentials(self):
        """
        Tests resume course when the last accessed sequential is deleted and
        there are no sequentials left in the vertical.

        """
        course = self.create_test_course()

        # first navigate to a sequential to make it the last accessed
        chapter = course.children[0]
        self.assertEqual(len(chapter.children), 2)
        sequential = chapter.children[0]
        self.visit_sequential(course, chapter, sequential)

        # remove all sequentials from chapter
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
            for sequential in chapter.children:
                self.store.delete_item(sequential.location, self.user.id)  # pylint: disable=no-member

        # check resume course buttons
        response = self.client.get(course_home_url(course))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Start Course', count=0)
        self.assertContains(response, 'Resume Course', count=1)


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
            sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
            ItemFactory.create(category='vertical', parent_location=sequential.location)
            chapter = ItemFactory.create(
                category='chapter',
                parent_location=course.location,
                display_name='Future Chapter',
                start=future_date,
            )
            sequential = ItemFactory.create(category='sequential', parent_location=chapter.location)
            ItemFactory.create(category='vertical', parent_location=sequential.location)

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
        self.assertContains(response, escape(expected_text))
