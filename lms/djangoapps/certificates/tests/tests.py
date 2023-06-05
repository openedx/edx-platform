"""
Tests for the certificates models.
"""


from datetime import datetime, timedelta

import six
from ddt import data, ddt, unpack
from django.conf import settings
from milestones.tests.utils import MilestonesTestCaseMixin
from mock import patch
from pytz import UTC

from lms.djangoapps.badges.tests.factories import CourseCompleteImageConfigurationFactory
from lms.djangoapps.certificates.models import (
    CertificateStatuses,
    GeneratedCertificate,
    certificate_info_for_user,
    certificate_status_for_student
)
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.util.milestones_helpers import milestones_achieved_by_user, set_prerequisite_courses
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt
class CertificatesModelTest(ModuleStoreTestCase, MilestonesTestCaseMixin):
    """
    Tests for the GeneratedCertificate model
    """

    def setUp(self):
        super(CertificatesModelTest, self).setUp()

        today = datetime.now(UTC)
        self.instructor_paced_course = CourseFactory.create(
            org='edx', number='instructor', display_name='Instructor Paced Course',
            start=today - timedelta(days=30),
            end=today - timedelta(days=2),
            certificate_available_date=today - timedelta(days=1),
            self_paced=False
        )
        self.self_paced_course = CourseFactory.create(
            org='edx', number='self',
            display_name='Self Paced Course', self_paced=True
        )

    def test_certificate_status_for_student(self):
        student = UserFactory()
        course = CourseFactory.create(org='edx', number='verified', display_name='Verified Course')

        certificate_status = certificate_status_for_student(student, course.id)
        self.assertEqual(certificate_status['status'], CertificateStatuses.unavailable)
        self.assertEqual(certificate_status['mode'], GeneratedCertificate.MODES.honor)

    @unpack
    @data(
        {'allow_certificate': False, 'whitelisted': False, 'grade': None, 'output': ['N', 'N', 'N/A']},
        {'allow_certificate': True, 'whitelisted': True, 'grade': None, 'output': ['Y', 'N', 'N/A']},
        {'allow_certificate': True, 'whitelisted': False, 'grade': 0.9, 'output': ['N', 'N', 'N/A']},
        {'allow_certificate': False, 'whitelisted': True, 'grade': 0.8, 'output': ['N', 'N', 'N/A']},
        {'allow_certificate': False, 'whitelisted': None, 'grade': 0.8, 'output': ['N', 'N', 'N/A']}
    )
    def test_certificate_info_for_user(self, allow_certificate, whitelisted, grade, output):
        """
        Verify that certificate_info_for_user works.
        """
        student = UserFactory()
        student.profile.allow_certificate = allow_certificate
        student.profile.save()

        # for instructor paced course
        certificate_info = certificate_info_for_user(
            student, self.instructor_paced_course.id, grade,
            whitelisted, user_certificate=None
        )
        self.assertEqual(certificate_info, output)

        # for self paced course
        certificate_info = certificate_info_for_user(
            student, self.self_paced_course.id, grade,
            whitelisted, user_certificate=None
        )
        self.assertEqual(certificate_info, output)

    @unpack
    @data(
        {'allow_certificate': False, 'whitelisted': False, 'grade': None, 'output': ['N', 'Y', 'honor']},
        {'allow_certificate': True, 'whitelisted': True, 'grade': None, 'output': ['Y', 'Y', 'honor']},
        {'allow_certificate': True, 'whitelisted': False, 'grade': 0.9, 'output': ['Y', 'Y', 'honor']},
        {'allow_certificate': False, 'whitelisted': True, 'grade': 0.8, 'output': ['N', 'Y', 'honor']},
        {'allow_certificate': False, 'whitelisted': None, 'grade': 0.8, 'output': ['N', 'Y', 'honor']},
        {'allow_certificate': True, 'whitelisted': None, 'grade': None, 'output': ['Y', 'Y', 'honor']},
        {'allow_certificate': False, 'whitelisted': True, 'grade': None, 'output': ['N', 'Y', 'honor']}
    )
    def test_certificate_info_for_user_when_grade_changes(self, allow_certificate, whitelisted, grade, output):
        """
        Verify that certificate_info_for_user works as expect in scenario when grading of problems
        changes after certificates already generated. In such scenario `Certificate delivered` should not depend
        on student's eligibility to get certificates since in above scenario eligibility can change over period
        of time.
        """
        student = UserFactory()
        student.profile.allow_certificate = allow_certificate
        student.profile.save()

        certificate1 = GeneratedCertificateFactory.create(
            user=student,
            course_id=self.instructor_paced_course.id,
            status=CertificateStatuses.downloadable,
            mode='honor'
        )

        certificate2 = GeneratedCertificateFactory.create(
            user=student,
            course_id=self.self_paced_course.id,
            status=CertificateStatuses.downloadable,
            mode='honor'
        )

        # for instructor paced course
        certificate_info = certificate_info_for_user(
            student, self.instructor_paced_course.id, grade,
            whitelisted, certificate1
        )
        self.assertEqual(certificate_info, output)

        # for self paced course
        certificate_info = certificate_info_for_user(
            student, self.self_paced_course.id, grade,
            whitelisted, certificate2
        )
        self.assertEqual(certificate_info, output)

    @unpack
    @data(
        {'allow_certificate': True, 'whitelisted': False, 'grade': 0.8, 'mode': 'audit', 'output': ['N', 'N', 'N/A']},
        {'allow_certificate': True, 'whitelisted': True, 'grade': 0.8, 'mode': 'audit', 'output': ['Y', 'N', 'N/A']},
        {'allow_certificate': True, 'whitelisted': False, 'grade': 0.8, 'mode': 'verified', 'output': ['Y', 'N', 'N/A']}
    )
    def test_certificate_info_for_user_with_course_modes(self, allow_certificate, whitelisted, grade, mode, output):
        """
        Verify that certificate_info_for_user works with course modes.
        """
        user = UserFactory.create()
        user.profile.allow_certificate = allow_certificate
        user.profile.save()
        _ = CourseEnrollment.enroll(user, self.instructor_paced_course.id, mode)
        certificate_info = certificate_info_for_user(
            user, self.instructor_paced_course.id, grade,
            whitelisted, user_certificate=None
        )
        self.assertEqual(certificate_info, output)

    def test_course_ids_with_certs_for_user(self):
        # Create one user with certs and one without
        student_no_certs = UserFactory()
        student_with_certs = UserFactory()
        student_with_certs.profile.allow_certificate = True
        student_with_certs.profile.save()

        # Set up a couple of courses
        course_1 = CourseFactory.create()
        course_2 = CourseFactory.create()

        # Generate certificates
        GeneratedCertificateFactory.create(
            user=student_with_certs,
            course_id=course_1.id,
            status=CertificateStatuses.downloadable,
            mode='honor'
        )
        GeneratedCertificateFactory.create(
            user=student_with_certs,
            course_id=course_2.id,
            status=CertificateStatuses.downloadable,
            mode='honor'
        )

        # User with no certs should return an empty set.
        self.assertSetEqual(
            GeneratedCertificate.course_ids_with_certs_for_user(student_no_certs),
            set()
        )
        # User with certs should return a set with the two course_ids
        self.assertSetEqual(
            GeneratedCertificate.course_ids_with_certs_for_user(student_with_certs),
            {course_1.id, course_2.id}
        )

    @patch.dict(settings.FEATURES, {'ENABLE_PREREQUISITE_COURSES': True})
    def test_course_milestone_collected(self):
        student = UserFactory()
        course = CourseFactory.create(org='edx', number='998', display_name='Test Course')
        pre_requisite_course = CourseFactory.create(org='edx', number='999', display_name='Pre requisite Course')
        # set pre-requisite course
        set_prerequisite_courses(course.id, [six.text_type(pre_requisite_course.id)])
        # get milestones collected by user before completing the pre-requisite course
        completed_milestones = milestones_achieved_by_user(student, six.text_type(pre_requisite_course.id))
        self.assertEqual(len(completed_milestones), 0)

        GeneratedCertificateFactory.create(
            user=student,
            course_id=pre_requisite_course.id,
            status=CertificateStatuses.generating,
            mode='verified'
        )
        # get milestones collected by user after user has completed the pre-requisite course
        completed_milestones = milestones_achieved_by_user(student, six.text_type(pre_requisite_course.id))
        self.assertEqual(len(completed_milestones), 1)
        self.assertEqual(completed_milestones[0]['namespace'], six.text_type(pre_requisite_course.id))

    @patch.dict(settings.FEATURES, {'ENABLE_OPENBADGES': True})
    @patch('lms.djangoapps.badges.backends.badgr.BadgrBackend', spec=True)
    def test_badge_callback(self, handler):
        student = UserFactory()
        course = CourseFactory.create(org='edx', number='998', display_name='Test Course', issue_badges=True)
        CourseCompleteImageConfigurationFactory()
        CourseEnrollmentFactory(user=student, course_id=course.location.course_key, mode='honor')
        cert = GeneratedCertificateFactory.create(
            user=student,
            course_id=course.id,
            status=CertificateStatuses.generating,
            mode='verified'
        )
        cert.status = CertificateStatuses.downloadable
        cert.save()
        self.assertTrue(handler.return_value.award.called)
