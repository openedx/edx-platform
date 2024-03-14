"""
Unit tests for reset_student_course task
"""

from unittest.mock import patch, Mock, call

from xmodule.modulestore.tests.factories import BlockFactory

from lms.djangoapps.courseware.tests.test_submitting_problems import TestSubmittingProblems
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.support.tasks import reset_student_course
from lms.djangoapps.support.tests.factories import CourseResetAuditFactory, CourseResetCourseOptInFactory
from lms.djangoapps.support.models import CourseResetAudit
from common.djangoapps.student.models.course_enrollment import CourseEnrollment
from common.djangoapps.student.roles import SupportStaffRole
from common.djangoapps.student.tests.factories import UserFactory


class ResetStudentCourse(TestSubmittingProblems):
    """ Test reset_student_course task """
    USERNAME = "support"
    EMAIL = "support@example.com"
    PASSWORD = "support"

    def setUp(self):
        """
        Set permissions, create a course and learner, enroll learner and opt into course reset
        """
        super().setUp()
        self.user = UserFactory(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        SupportStaffRole().add_users(self.user)
        self.course_id = str(self.course.id)
        self.enrollment = CourseEnrollment.objects.filter(user=self.student_user, course_id=self.course.id).first()
        self.opt_in = CourseResetCourseOptInFactory.create(course_id=self.course.id)
        self.audit = CourseResetAuditFactory.create(
            course=self.opt_in,
            course_enrollment=self.enrollment,
            reset_by=self.user,
            status=CourseResetAudit.CourseResetStatus.ENQUEUED
        )
        self.p1 = ''
        self.p2 = ''
        self.p3 = ''

    def basic_setup(self):
        """
        Set up a simple course for testing basic grading functionality.
        """
        grading_policy = {
            "GRADER": [{
                "type": "Homework",
                "min_count": 1,
                "drop_count": 0,
                "short_label": "HW",
                "weight": 1.0
            }],
            "GRADE_CUTOFFS": {
                'A': .9,
                'B': .33
            }
        }
        self.add_grading_policy(grading_policy)

        # set up a simple course with four problems
        homework = self.add_graded_section_to_course('homework')
        vertical = BlockFactory.create(
            parent_location=homework.location,
            category='vertical',
            display_name='Unit 1',
        )

        self.p1 = self.add_dropdown_to_section(vertical.location, 'p1', 1)
        self.p2 = self.add_dropdown_to_section(vertical.location, 'p2', 1)
        self.p3 = self.add_dropdown_to_section(vertical.location, 'p3', 1)

        self.refresh_course()

    def test_reset_student_course(self):
        """ Test that it resets student attempts  """
        with patch(
                'lms.djangoapps.support.tasks.reset_student_attempts',
        ) as mock_reset_student_attempts:
            self.basic_setup()
            reset_student_course(self.course_id, self.student_user.email, self.user.email)

            mock_reset_student_attempts.assert_has_calls([
                call(
                    self.course.id,
                    self.student_user,
                    self.p1.location,
                    self.user,
                    True
                ),
                call(
                    self.course.id,
                    self.student_user,
                    self.p2.location,
                    self.user,
                    True
                ),
                call(
                    self.course.id,
                    self.student_user,
                    self.p3.location,
                    self.user,
                    True
                )
            ])

            course_reset_audit = CourseResetAudit.objects.get(course_enrollment=self.enrollment)
            self.assertIsNotNone(course_reset_audit.completed_at)
            self.assertEqual(course_reset_audit.status, CourseResetAudit.CourseResetStatus.COMPLETE)

    def test_reset_student_course_student_module_not_found(self):

        with patch(
                'lms.djangoapps.support.tasks.reset_student_attempts',
                Mock(side_effect=StudentModule.DoesNotExist())
        ) as mock_reset_student_attempts:
            self.basic_setup()
            reset_student_course(self.course_id, self.student_user.email, self.user.email)
            mock_reset_student_attempts.assert_has_calls([
                call(
                    self.course.id,
                    self.student_user,
                    self.p1.location,
                    self.user,
                    True
                ),
                call(
                    self.course.id,
                    self.student_user,
                    self.p2.location,
                    self.user,
                    True
                ),
                call(
                    self.course.id,
                    self.student_user,
                    self.p3.location,
                    self.user,
                    True
                )
            ])

            course_reset_audit = CourseResetAudit.objects.get(course_enrollment=self.enrollment)
            self.assertRaises(StudentModule.DoesNotExist, mock_reset_student_attempts)
            self.assertIsNotNone(course_reset_audit.completed_at)
            self.assertEqual(course_reset_audit.status, CourseResetAudit.CourseResetStatus.COMPLETE)

    @patch('lms.djangoapps.support.tasks.reset_student_attempts')
    def test_reset_student_course_fail(self, mock_reset_student_attempts):
        with patch(
                'lms.djangoapps.support.tasks.get_blocks',
                Mock(side_effect=Exception())
        ):
            reset_student_course(self.course_id, self.student_user.email, self.user.email)
            mock_reset_student_attempts.assert_not_called()
            course_reset_audit = CourseResetAudit.objects.get(course_enrollment=self.enrollment)
            self.assertIsNone(course_reset_audit.completed_at)
            self.assertEqual(course_reset_audit.status, CourseResetAudit.CourseResetStatus.FAILED)

    def test_reset_student_attempts_raise_exception(self):
        with patch(
                'lms.djangoapps.support.tasks.reset_student_attempts',
                Mock(side_effect=Exception())
        ) as mock_reset_student_attempts:
            self.basic_setup()
            reset_student_course(self.course_id, self.student_user.email, self.user.email)
            mock_reset_student_attempts.assert_called_once()
            course_reset_audit = CourseResetAudit.objects.get(course_enrollment=self.enrollment)
            self.assertIsNone(course_reset_audit.completed_at)
            self.assertEqual(course_reset_audit.status, CourseResetAudit.CourseResetStatus.FAILED)
