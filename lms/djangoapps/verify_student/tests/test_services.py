"""
Tests of re-verification service.
"""

import ddt

from course_modes.tests.factories import CourseModeFactory
from student.tests.factories import UserFactory
from verify_student.models import VerificationCheckpoint, VerificationStatus, SkippedReverification
from verify_student.services import ReverificationService

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
        course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        self.course_key = course.id
        CourseModeFactory(
            mode_slug="verified",
            course_id=self.course_key,
            min_price=100,
        )
        self.item = ItemFactory.create(parent=course, category='chapter', display_name='Test Section')
        self.final_checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/final_uuid'.format(
            org=self.course_key.org, course=self.course_key.course
        )

    @ddt.data('final', 'midterm')
    def test_start_verification(self, checkpoint_name):
        """Test the 'start_verification' service method.

        Check that if a reverification checkpoint exists for a specific course
        then 'start_verification' method returns that checkpoint otherwise it
        creates that checkpoint.
        """
        reverification_service = ReverificationService()
        checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/{checkpoint}'.format(
            org=self.course_key.org, course=self.course_key.course, checkpoint=checkpoint_name
        )
        expected_url = (
            '/verify_student/reverify'
            '/{course_key}'
            '/{checkpoint_location}/'
        ).format(course_key=unicode(self.course_key), checkpoint_location=checkpoint_location)

        self.assertEqual(
            reverification_service.start_verification(unicode(self.course_key), checkpoint_location),
            expected_url
        )

    def test_get_status(self):
        """Test the verification statuses of a user for a given 'checkpoint'
        and 'course_id'.
        """
        reverification_service = ReverificationService()
        self.assertIsNone(
            reverification_service.get_status(self.user.id, unicode(self.course_key), self.final_checkpoint_location)
        )

        checkpoint_obj = VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_key),
            checkpoint_location=self.final_checkpoint_location
        )
        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status='submitted')
        self.assertEqual(
            reverification_service.get_status(self.user.id, unicode(self.course_key), self.final_checkpoint_location),
            'submitted'
        )

        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status='approved')
        self.assertEqual(
            reverification_service.get_status(self.user.id, unicode(self.course_key), self.final_checkpoint_location),
            'approved'
        )

    def test_skip_verification(self):
        """
        Test adding skip attempt of a user for a reverification checkpoint.
        """
        reverification_service = ReverificationService()
        VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_key),
            checkpoint_location=self.final_checkpoint_location
        )

        reverification_service.skip_verification(self.user.id, unicode(self.course_key), self.final_checkpoint_location)
        self.assertEqual(
            SkippedReverification.objects.filter(user=self.user, course_id=self.course_key).count(),
            1
        )

        # now test that a user can have only one entry for a skipped
        # reverification for a course
        reverification_service.skip_verification(self.user.id, unicode(self.course_key), self.final_checkpoint_location)
        self.assertEqual(
            SkippedReverification.objects.filter(user=self.user, course_id=self.course_key).count(),
            1
        )

    def test_get_attempts(self):
        """Check verification attempts count against a user for a given
        'checkpoint' and 'course_id'.
        """
        reverification_service = ReverificationService()
        course_id = unicode(self.course_key)
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
