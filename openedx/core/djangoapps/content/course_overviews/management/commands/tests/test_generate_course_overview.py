"""
Tests that the generate_course_overview management command actually generates course overviews.
"""


import six
from django.core.management.base import CommandError
from mock import patch

from openedx.core.djangoapps.content.course_overviews.management.commands import generate_course_overview
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestGenerateCourseOverview(ModuleStoreTestCase):
    """
    Tests course overview management command.
    """

    def setUp(self):
        """
        Create courses in modulestore.
        """
        super(TestGenerateCourseOverview, self).setUp()
        self.course_key_1 = CourseFactory.create().id
        self.course_key_2 = CourseFactory.create().id
        self.command = generate_course_overview.Command()

    def _assert_courses_not_in_overview(self, *courses):
        """
        Assert that courses doesn't exist in the course overviews.
        """
        course_keys = CourseOverview.get_all_course_keys()
        for expected_course_key in courses:
            self.assertNotIn(expected_course_key, course_keys)

    def _assert_courses_in_overview(self, *courses):
        """
        Assert courses exists in course overviews.
        """
        course_keys = CourseOverview.get_all_course_keys()
        for expected_course_key in courses:
            self.assertIn(expected_course_key, course_keys)

    def test_generate_all(self):
        """
        Test that all courses in the modulestore are loaded into course overviews.
        """
        # ensure that the newly created courses aren't in course overviews
        self._assert_courses_not_in_overview(self.course_key_1, self.course_key_2)
        self.command.handle(all_courses=True)

        # CourseOverview will be populated with all courses in the modulestore
        self._assert_courses_in_overview(self.course_key_1, self.course_key_2)

    def test_generate_one(self):
        """
        Test that a specified course is loaded into course overviews.
        """
        self._assert_courses_not_in_overview(self.course_key_1, self.course_key_2)
        self.command.handle(six.text_type(self.course_key_1), all_courses=False)
        self._assert_courses_in_overview(self.course_key_1)
        self._assert_courses_not_in_overview(self.course_key_2)

    def test_generate_force_update(self):
        self.command.handle(all_courses=True)

        # update each course
        updated_course_name = u'test_generate_course_overview.course_edit'
        for course_key in (self.course_key_1, self.course_key_2):
            course = self.store.get_course(course_key)
            course.display_name = updated_course_name
            self.store.update_item(course, self.user.id)

        # force_update course_key_1, but not course_key_2
        self.command.handle(six.text_type(self.course_key_1), all_courses=False, force_update=True)
        self.command.handle(six.text_type(self.course_key_2), all_courses=False, force_update=False)

        self.assertEqual(CourseOverview.get_from_id(self.course_key_1).display_name, updated_course_name)
        self.assertNotEqual(CourseOverview.get_from_id(self.course_key_2).display_name, updated_course_name)

    def test_invalid_key(self):
        """
        Test that CommandError is raised for invalid key.
        """
        with self.assertRaises(CommandError):
            self.command.handle('not/found', all_courses=False)

    @patch('openedx.core.djangoapps.content.course_overviews.models.log')
    def test_not_found_key(self, mock_log):
        """
        Test keys not found are logged.
        """
        self.command.handle('fake/course/id', all_courses=False)
        self.assertTrue(mock_log.exception.called)

    def test_no_params(self):
        """
        Test exception raised when no parameters are specified.
        """
        with self.assertRaises(CommandError):
            self.command.handle(all_courses=False)

    @patch('openedx.core.djangoapps.content.course_overviews.tasks.async_course_overview_update')
    def test_routing_key(self, mock_async_task):
        self.command.handle(all_courses=True, force_update=True, routing_key='my-routing-key', chunk_size=10000)

        called_kwargs = mock_async_task.apply_async.call_args_list[0][1]
        self.assertEqual(
            sorted([six.text_type(self.course_key_1), six.text_type(self.course_key_2)]),
            sorted(called_kwargs.pop('args'))
        )
        self.assertEqual({
            'kwargs': {'force_update': True},
            'routing_key': 'my-routing-key'
        }, called_kwargs
        )
        self.assertEqual(1, mock_async_task.apply_async.call_count)
