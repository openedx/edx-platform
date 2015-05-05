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

    @ddt.data("final_term", "mid_term")
    def test_start_verification(self, checkpoint_name):
        """
        Test the 'start_verification' service method. If checkpoint exists for
        a specific course then return the checkpoint otherwise create that
        checkpoint.
        """
        reverification_service = ReverificationService()
        reverification_service.start_verification(unicode(self.course_key), checkpoint_name, self.item.location)
        expected_url = (
            '/verify_student/reverify'
            '/{course_key}'
            '/{checkpoint_name}'
            '/{usage_id}/'
        ).format(course_key=unicode(self.course_key), checkpoint_name=checkpoint_name, usage_id=self.item.location)

        self.assertEqual(
            expected_url,
            reverification_service.start_verification(unicode(self.course_key), checkpoint_name, self.item.location)
        )

    def test_get_status(self):
        """
        Test the verification statuses of a user for a given 'checkpoint' and
        'course_id'.
        """
        checkpoint_name = 'final_term'
        reverification_service = ReverificationService()
        self.assertIsNone(reverification_service.get_status(self.user.id, unicode(self.course_key), checkpoint_name))

        checkpoint_obj = VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_key),
            checkpoint_name=checkpoint_name
        )

        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status='submitted')
        self.assertEqual(
            reverification_service.get_status(self.user.id, unicode(self.course_key), checkpoint_name),
            'submitted'
        )

        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status='submitted')
        self.assertEqual(
            reverification_service.get_status(self.user.id, unicode(self.course_key), checkpoint_name),
            'submitted'
        )

    def test_skip_verification(self):
        """
        Adding the test skip verification attempt for the user
        """
        checkpoint_name = 'final_term'
        reverification_service = ReverificationService()
        VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_key),
            checkpoint_name=checkpoint_name
        )

        reverification_service.skip_verification(checkpoint_name, self.user.id, unicode(self.course_key))
        self.assertEqual(1, SkippedReverification.objects.filter(user=self.user, course_id=self.course_key).count())

        reverification_service.skip_verification(checkpoint_name, self.user.id, unicode(self.course_key))
        self.assertEqual(1, SkippedReverification.objects.filter(user=self.user, course_id=self.course_key).count())

    def test_get_attempts(self):
        """
        Check verification attempts count against a user for a given
        'checkpoint' and 'course_id'.
        """
        checkpoint_name = 'final_term'
        reverification_service = ReverificationService()
        course_id = unicode(self.course_key)
        self.assertEqual(
            reverification_service.get_attempts(self.user.id, course_id, checkpoint_name, location_id=None),
            0
        )

        # now create a checkpoint and add user's entry against it then test
        # that the 'get_attempts' service method returns count accordingly
        checkpoint_obj = VerificationCheckpoint.objects.create(course_id=course_id, checkpoint_name=checkpoint_name)
        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status='submitted')
        self.assertEqual(
            reverification_service.get_attempts(self.user.id, course_id, checkpoint_name, location_id=None),
            1
        )
