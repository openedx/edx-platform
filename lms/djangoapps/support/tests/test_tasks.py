"""
Unit tests for reset_student_course task
"""


from datetime import datetime, timedelta
from pytz import UTC

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory

from lms.djangoapps.support.tasks import reset_student_course
from lms.djangoapps.support.tests.factories import CourseResetAuditFactory, CourseResetCourseOptInFactory
from lms.djangoapps.support.models import CourseResetAudit
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from common.djangoapps.student.roles import SupportStaffRole
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory


class ResetStudentCourse(ModuleStoreTestCase):
    """ Test expire_waiting_enrollments task """
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
        self.now = datetime.now().replace(tzinfo=UTC)

        self.course = CourseFactory.create(
            start=self.now - timedelta(days=90),
            end=self.now + timedelta(days=90),
        )
        self.course_id = str(self.course.id)
        self.course_overview = CourseOverview.get_from_id(self.course.id)
        self.learner = UserFactory.create()
        self.enrollment = CourseEnrollmentFactory.create(user=self.learner, course_id=self.course.id)
        self.opt_in = CourseResetCourseOptInFactory.create(course_id=self.course.id)
        self.audit = CourseResetAuditFactory.create(
            course=self.opt_in,
            course_enrollment=self.enrollment,
            reset_by=self.user,
            status=CourseResetAudit.CourseResetStatus.FAILED
        )

    def test_reset_student_course(self):
        reset_student_course(self.course_id, self.learner.email, self.user.email)
        course_reset_audit = CourseResetAudit.objects.filter(course_enrollment=self.enrollment).first()
        self.assertTrue(course_reset_audit.completed_at)
