"""
Tests for the InstructorService
"""

import json
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.models import StudentModule
from instructor.services import InstructorService
from instructor.tests.test_tools import msk_from_problem_urlname
from nose.plugins.attrib import attr

from student.models import CourseEnrollment
from student.tests.factories import UserFactory


@attr('shard_1')
class InstructorServiceTests(ModuleStoreTestCase):
    """
    Tests for the InstructorService
    """

    def setUp(self):
        super(InstructorServiceTests, self).setUp()

        self.course = CourseFactory.create()
        self.student = UserFactory()
        CourseEnrollment.enroll(self.student, self.course.id)

        self.problem_location = msk_from_problem_urlname(
            self.course.id,
            'robot-some-problem-urlname'
        )

        self.other_problem_location = msk_from_problem_urlname(
            self.course.id,
            'robot-some-other_problem-urlname'
        )

        self.problem_urlname = unicode(self.problem_location)
        self.other_problem_urlname = unicode(self.other_problem_location)

        self.service = InstructorService()
        self.module_to_reset = StudentModule.objects.create(
            student=self.student,
            course_id=self.course.id,
            module_state_key=self.problem_location,
            state=json.dumps({'attempts': 2}),
        )

    def test_reset_student_attempts_delete(self):
        """
        Test delete student state.
        """

        # make sure the attempt is there
        self.assertEqual(
            StudentModule.objects.filter(
                student=self.module_to_reset.student,
                course_id=self.course.id,
                module_state_key=self.module_to_reset.module_state_key,
            ).count(),
            1
        )

        self.service.delete_student_attempt(
            self.student.username,
            unicode(self.course.id),
            self.problem_urlname
        )

        # make sure the module has been deleted
        self.assertEqual(
            StudentModule.objects.filter(
                student=self.module_to_reset.student,
                course_id=self.course.id,
                module_state_key=self.module_to_reset.module_state_key,
            ).count(),
            0
        )

    def test_reset_bad_content_id(self):
        """
        Negative test of trying to reset attempts with bad content_id
        """

        result = self.service.delete_student_attempt(
            self.student.username,
            unicode(self.course.id),
            'foo/bar/baz'
        )
        self.assertIsNone(result)

    def test_reset_bad_user(self):
        """
        Negative test of trying to reset attempts with bad user identifier
        """

        result = self.service.delete_student_attempt(
            'bad_student',
            unicode(self.course.id),
            'foo/bar/baz'
        )
        self.assertIsNone(result)

    def test_reset_non_existing_attempt(self):
        """
        Negative test of trying to reset attempts with bad user identifier
        """

        result = self.service.delete_student_attempt(
            self.student.username,
            unicode(self.course.id),
            self.other_problem_urlname
        )
        self.assertIsNone(result)
