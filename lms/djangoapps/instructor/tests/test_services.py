"""
Tests for the InstructorService
"""

import json
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.models import StudentModule
from instructor.access import allow_access
from instructor.services import InstructorService
from instructor.tests.test_tools import msk_from_problem_urlname
from nose.plugins.attrib import attr

from student.models import CourseEnrollment
from student.tests.factories import UserFactory


@attr('shard_1')
class InstructorServiceTests(SharedModuleStoreTestCase):
    """
    Tests for the InstructorService
    """
    @classmethod
    def setUpClass(cls):
        super(InstructorServiceTests, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.problem_location = msk_from_problem_urlname(
            cls.course.id,
            'robot-some-problem-urlname'
        )
        cls.other_problem_location = msk_from_problem_urlname(
            cls.course.id,
            'robot-some-other_problem-urlname'
        )
        cls.problem_urlname = unicode(cls.problem_location)
        cls.other_problem_urlname = unicode(cls.other_problem_location)

    def setUp(self):
        super(InstructorServiceTests, self).setUp()

        self.student = UserFactory()
        CourseEnrollment.enroll(self.student, self.course.id)

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

    def test_is_user_staff(self):
        """
        Test to assert that the usrr is staff or not
        """
        result = self.service.is_course_staff(
            self.student,
            unicode(self.course.id)
        )
        self.assertFalse(result)

        # allow staff access to the student
        allow_access(self.course, self.student, 'staff')
        result = self.service.is_course_staff(
            self.student,
            unicode(self.course.id)
        )
        self.assertTrue(result)
