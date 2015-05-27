"""
Tests for the certificates models.
"""

from mock import patch
from django.conf import settings

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from student.tests.factories import UserFactory
from certificates.models import CertificateStatuses, GeneratedCertificate, certificate_status_for_student
from certificates.tests.factories import GeneratedCertificateFactory

from util.milestones_helpers import (
    set_prerequisite_courses,
    milestones_achieved_by_user,
    seed_milestone_relationship_types,
)


class CertificatesModelTest(ModuleStoreTestCase):
    """
    Tests for the GeneratedCertificate model
    """

    def test_certificate_status_for_student(self):
        student = UserFactory()
        course = CourseFactory.create(org='edx', number='verified', display_name='Verified Course')

        certificate_status = certificate_status_for_student(student, course.id)
        self.assertEqual(certificate_status['status'], CertificateStatuses.unavailable)
        self.assertEqual(certificate_status['mode'], GeneratedCertificate.MODES.honor)

    @patch.dict(settings.FEATURES, {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_course_milestone_collected(self):
        seed_milestone_relationship_types()
        student = UserFactory()
        course = CourseFactory.create(org='edx', number='998', display_name='Test Course')
        pre_requisite_course = CourseFactory.create(org='edx', number='999', display_name='Pre requisite Course')
        # set pre-requisite course
        set_prerequisite_courses(course.id, [unicode(pre_requisite_course.id)])
        # get milestones collected by user before completing the pre-requisite course
        completed_milestones = milestones_achieved_by_user(student, unicode(pre_requisite_course.id))
        self.assertEqual(len(completed_milestones), 0)

        GeneratedCertificateFactory.create(
            user=student,
            course_id=pre_requisite_course.id,
            status=CertificateStatuses.generating,
            mode='verified'
        )
        # get milestones collected by user after user has completed the pre-requisite course
        completed_milestones = milestones_achieved_by_user(student, unicode(pre_requisite_course.id))
        self.assertEqual(len(completed_milestones), 1)
        self.assertEqual(completed_milestones[0]['namespace'], unicode(pre_requisite_course.id))
