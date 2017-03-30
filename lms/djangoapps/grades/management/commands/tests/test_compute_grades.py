"""
Tests for compute_grades management command.
"""

# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function, unicode_literals

import ddt
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from mock import patch
import six

from student.models import CourseEnrollment
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from lms.djangoapps.grades.config.models import ComputeGradesSetting
from lms.djangoapps.grades.management.commands import compute_grades


@ddt.ddt
class TestComputeGrades(SharedModuleStoreTestCase):
    """
    Tests compute_grades management command.
    """
    num_users = 3
    num_courses = 5

    @classmethod
    def setUpClass(cls):
        super(TestComputeGrades, cls).setUpClass()
        User = get_user_model()  # pylint: disable=invalid-name
        cls.command = compute_grades.Command()

        cls.courses = [CourseFactory.create() for _ in range(cls.num_courses)]
        cls.course_keys = [six.text_type(course.id) for course in cls.courses]
        cls.users = [User.objects.create(username='user{}'.format(idx)) for idx in range(cls.num_users)]

        for user in cls.users:
            for course in cls.courses:
                CourseEnrollment.enroll(user, course.id)

    def test_select_all_courses(self):
        courses = self.command._get_course_keys({'all_courses': True})
        self.assertEqual(
            sorted(six.text_type(course) for course in courses),
            self.course_keys,
        )

    def test_specify_courses(self):
        courses = self.command._get_course_keys({'courses': [self.course_keys[0], self.course_keys[1], 'd/n/e']})
        self.assertEqual(
            [six.text_type(course) for course in courses],
            [self.course_keys[0], self.course_keys[1], 'd/n/e'],
        )

    def test_selecting_invalid_course(self):
        with self.assertRaises(CommandError):
            self.command._get_course_keys({'courses': [self.course_keys[0], self.course_keys[1], 'badcoursekey']})

    def test_from_settings(self):
        ComputeGradesSetting.objects.create(course_ids=" ".join(self.course_keys))
        courses = self.command._get_course_keys({'from_settings': True})
        self.assertEqual(
            sorted(six.text_type(course) for course in courses),
            self.course_keys,
        )
        # test that --from_settings always uses the latest setting
        ComputeGradesSetting.objects.create(course_ids='badcoursekey')
        with self.assertRaises(CommandError):
            self.command._get_course_keys({'from_settings': True})

    @patch('lms.djangoapps.grades.tasks.compute_grades_for_course')
    def test_tasks_fired(self, mock_task):
        call_command(
            'compute_grades',
            '--routing_key=key',
            '--batch_size=2',
            '--courses',
            self.course_keys[0],
            self.course_keys[3],
            'd/n/e'  # No tasks created for nonexistent course, because it has no enrollments
        )
        self.assertEqual(
            mock_task.apply_async.call_args_list,
            [
                ({
                    'options': {'routing_key': 'key'},
                    'kwargs': {'course_key': self.course_keys[0], 'batch_size': 2, 'offset': 0}
                },),
                ({
                    'options': {'routing_key': 'key'},
                    'kwargs': {'course_key': self.course_keys[0], 'batch_size': 2, 'offset': 2}
                },),
                ({
                    'options': {'routing_key': 'key'},
                    'kwargs': {'course_key': self.course_keys[3], 'batch_size': 2, 'offset': 0}
                },),
                ({
                    'options': {'routing_key': 'key'},
                    'kwargs': {'course_key': self.course_keys[3], 'batch_size': 2, 'offset': 2}
                },),
            ],
        )
