"""
Tests of re-verification service.
"""

import ddt

from opaque_keys.edx.keys import CourseKey

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from lms.djangoapps.verify_student.models import VerificationCheckpoint, VerificationStatus, SkippedReverification
from lms.djangoapps.verify_student.services import ReverificationService

from openedx.core.djangoapps.credit.api import get_credit_requirement_status, set_credit_requirements
from openedx.core.djangoapps.credit.models import CreditCourse
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@ddt.ddt
class TestReverificationService(ModuleStoreTestCase):
    """
    Tests for the re-verification service.
    """

    def setUp(self):
        super(TestReverificationService, self).setUp()

        self.user = UserFactory.create(username="rusty", password="test")
        self.course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        self.course_id = self.course.id
        CourseModeFactory(
            mode_slug="verified",
            course_id=self.course_id,
            min_price=100,
        )
        self.course_key = CourseKey.from_string(unicode(self.course_id))

        self.item = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        self.final_checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/final_uuid'.format(
            org=self.course_id.org, course=self.course_id.course
        )

        # Enroll in a verified mode
        self.enrollment = CourseEnrollment.enroll(self.user, self.course_id, mode=CourseMode.VERIFIED)

    @ddt.data('final', 'midterm')
    def test_start_verification(self, checkpoint_name):
        """Test the 'start_verification' service method.

        Check that if a reverification checkpoint exists for a specific course
        then 'start_verification' method returns that checkpoint otherwise it
        creates that checkpoint.
        """
        reverification_service = ReverificationService()
        checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/{checkpoint}'.format(
            org=self.course_id.org, course=self.course_id.course, checkpoint=checkpoint_name
        )
        expected_url = (
            '/verify_student/reverify'
            '/{course_key}'
            '/{checkpoint_location}/'
        ).format(course_key=unicode(self.course_id), checkpoint_location=checkpoint_location)

        self.assertEqual(
            reverification_service.start_verification(unicode(self.course_id), checkpoint_location),
            expected_url
        )

    def test_get_status(self):
        """Test the verification statuses of a user for a given 'checkpoint'
        and 'course_id'.
        """
        reverification_service = ReverificationService()
        self.assertIsNone(
            reverification_service.get_status(self.user.id, unicode(self.course_id), self.final_checkpoint_location)
        )

        checkpoint_obj = VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_id),
            checkpoint_location=self.final_checkpoint_location
        )
        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status='submitted')
        self.assertEqual(
            reverification_service.get_status(self.user.id, unicode(self.course_id), self.final_checkpoint_location),
            'submitted'
        )

        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status='approved')
        self.assertEqual(
            reverification_service.get_status(self.user.id, unicode(self.course_id), self.final_checkpoint_location),
            'approved'
        )

    def test_skip_verification(self):
        """
        Test adding skip attempt of a user for a reverification checkpoint.
        """
        reverification_service = ReverificationService()
        VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_id),
            checkpoint_location=self.final_checkpoint_location
        )

        reverification_service.skip_verification(self.user.id, unicode(self.course_id), self.final_checkpoint_location)
        self.assertEqual(
            SkippedReverification.objects.filter(user=self.user, course_id=self.course_id).count(),
            1
        )

        # now test that a user can have only one entry for a skipped
        # reverification for a course
        reverification_service.skip_verification(self.user.id, unicode(self.course_id), self.final_checkpoint_location)
        self.assertEqual(
            SkippedReverification.objects.filter(user=self.user, course_id=self.course_id).count(),
            1
        )

        # testing service for skipped attempt.
        self.assertEqual(
            reverification_service.get_status(self.user.id, unicode(self.course_id), self.final_checkpoint_location),
            'skipped'
        )

    def test_declined_verification_on_skip(self):
        """Test that status with value 'declined' is added in credit
        requirement status model when a user skip's an ICRV.
        """
        reverification_service = ReverificationService()
        checkpoint = VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_id),
            checkpoint_location=self.final_checkpoint_location
        )
        # Create credit course and set credit requirements.
        CreditCourse.objects.create(course_key=self.course_key, enabled=True)
        set_credit_requirements(
            self.course_key,
            [
                {
                    "namespace": "reverification",
                    "name": checkpoint.checkpoint_location,
                    "display_name": "Assessment 1",
                    "criteria": {},
                }
            ]
        )

        reverification_service.skip_verification(self.user.id, unicode(self.course_id), self.final_checkpoint_location)
        requirement_status = get_credit_requirement_status(
            self.course_key, self.user.username, 'reverification', checkpoint.checkpoint_location
        )
        self.assertEqual(SkippedReverification.objects.filter(user=self.user, course_id=self.course_id).count(), 1)
        self.assertEqual(len(requirement_status), 1)
        self.assertEqual(requirement_status[0].get('name'), checkpoint.checkpoint_location)
        self.assertEqual(requirement_status[0].get('status'), 'declined')

    def test_get_attempts(self):
        """Check verification attempts count against a user for a given
        'checkpoint' and 'course_id'.
        """
        reverification_service = ReverificationService()
        course_id = unicode(self.course_id)
        self.assertEqual(
            reverification_service.get_attempts(self.user.id, course_id, self.final_checkpoint_location),
            0
        )

        # now create a checkpoint and add user's entry against it then test
        # that the 'get_attempts' service method returns correct count
        checkpoint_obj = VerificationCheckpoint.objects.create(
            course_id=course_id,
            checkpoint_location=self.final_checkpoint_location
        )
        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status='submitted')
        self.assertEqual(
            reverification_service.get_attempts(self.user.id, course_id, self.final_checkpoint_location),
            1
        )

    def test_not_in_verified_track(self):
        # No longer enrolled in a verified track
        self.enrollment.update_enrollment(mode=CourseMode.HONOR)

        # Should be marked as "skipped" (opted out)
        service = ReverificationService()
        status = service.get_status(self.user.id, unicode(self.course_id), self.final_checkpoint_location)
        self.assertEqual(status, service.NON_VERIFIED_TRACK)
