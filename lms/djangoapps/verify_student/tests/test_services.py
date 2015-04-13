# encoding: utf-8
"""
Tests of reverify service.
"""
import ddt
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from student.tests.factories import UserFactory
from course_modes.tests.factories import CourseModeFactory
from verify_student.services import ReverificationService
from verify_student.models import VerificationCheckpoint, VerificationStatus


@ddt.ddt
class TestReverifyService(ModuleStoreTestCase):
    """
    Tests for the re-verification service
    """

    def setUp(self):
        super(TestReverifyService, self).setUp()

        self.user = UserFactory.create(username="rusty", password="test")
        course = CourseFactory.create(org='Robot', number='999', display_name='Test Course')
        self.course_key = course.id
        CourseModeFactory(
            mode_slug="verified",
            course_id=self.course_key,
            min_price=100,
            suggested_prices=''
        )
        self.item = ItemFactory.create(parent=course, category='chapter', display_name='Test Section')

    @ddt.data("final_term", "mid_term")
    def test_start_verification(self, checkpoint_name):
        """Testing start verification service. If checkpoint exists for specific course then returns the checkpoint
        otherwise created that checkpoint.
        """

        rev = ReverificationService()
        rev.start_verification(unicode(self.course_key), checkpoint_name, self.item.location)
        expected_url = (
            '/verify_student/reverify'
            '/{course_key}'
            '/{checkpoint_name}'
            '/{usage_id}/'
        ).format(course_key=unicode(self.course_key), checkpoint_name=checkpoint_name, usage_id=self.item.location)

        self.assertEqual(
            expected_url, rev.start_verification(unicode(self.course_key), checkpoint_name, self.item.location)
        )

    def test_get_status(self):
        """ Check if the user has any verification attempt for the checkpoint and course_id """

        checkpoint_name = 'final_term'
        rev = ReverificationService()
        self.assertIsNone(rev.get_status(self.user.id, unicode(self.course_key), checkpoint_name))
        checkpoint_obj = VerificationCheckpoint.objects.create(
            course_id=unicode(self.course_key), checkpoint_name=checkpoint_name
        )

        VerificationStatus.objects.create(checkpoint=checkpoint_obj, user=self.user, status='submitted')
        self.assertEqual(rev.get_status(self.user.id, unicode(self.course_key), checkpoint_name), 'submitted')
