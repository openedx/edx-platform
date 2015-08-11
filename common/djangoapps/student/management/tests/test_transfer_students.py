"""
Tests the transfer student management command
"""
from django.conf import settings
from mock import patch, call
from opaque_keys.edx import locator
import unittest
import ddt

from shoppingcart.models import Order, CertificateItem  # pylint: disable=import-error
from course_modes.models import CourseMode
from student.management.commands import transfer_students
from student.models import CourseEnrollment, UNENROLL_DONE, EVENT_NAME_ENROLLMENT_DEACTIVATED, \
    EVENT_NAME_ENROLLMENT_ACTIVATED, EVENT_NAME_ENROLLMENT_MODE_CHANGED
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@ddt.ddt
class TestTransferStudents(ModuleStoreTestCase):
    """Tests for transferring students between courses."""

    PASSWORD = 'test'
    signal_fired = False

    def setUp(self, **kwargs):
        """Connect a stub receiver, and analytics event tracking."""
        super(TestTransferStudents, self).setUp()

        UNENROLL_DONE.connect(self.assert_unenroll_signal)
        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(UNENROLL_DONE.disconnect, self.assert_unenroll_signal)

    def assert_unenroll_signal(self, skip_refund=False, **kwargs):   # pylint: disable=unused-argument
        """ Signal Receiver stub for testing that the unenroll signal was fired. """
        self.assertFalse(self.signal_fired)
        self.assertTrue(skip_refund)
        self.signal_fired = True

    def test_transfer_students(self):
        """ Verify the transfer student command works as intended. """
        student = UserFactory.create()
        student.set_password(self.PASSWORD)
        student.save()
        mode = 'verified'
        # Original Course
        original_course_location = locator.CourseLocator('Org0', 'Course0', 'Run0')
        course = self._create_course(original_course_location)
        # Enroll the student in 'verified'
        CourseEnrollment.enroll(student, course.id, mode="verified")

        # Create and purchase a verified cert for the original course.
        self._create_and_purchase_verified(student, course.id)

        # New Course 1
        course_location_one = locator.CourseLocator('Org1', 'Course1', 'Run1')
        new_course_one = self._create_course(course_location_one)

        # New Course 2
        course_location_two = locator.CourseLocator('Org2', 'Course2', 'Run2')
        new_course_two = self._create_course(course_location_two)
        original_key = unicode(course.id)
        new_key_one = unicode(new_course_one.id)
        new_key_two = unicode(new_course_two.id)

        # Run the actual management command
        transfer_students.Command().handle(
            source_course=original_key, dest_course_list=new_key_one + "," + new_key_two
        )
        self.assertTrue(self.signal_fired)

        # Confirm the analytics event was emitted.
        self.mock_tracker.emit.assert_has_calls(  # pylint: disable=maybe-no-member
            [
                call(
                    EVENT_NAME_ENROLLMENT_ACTIVATED,
                    {'course_id': original_key, 'user_id': student.id, 'mode': mode}
                ),
                call(
                    EVENT_NAME_ENROLLMENT_MODE_CHANGED,
                    {'course_id': original_key, 'user_id': student.id, 'mode': mode}
                ),
                call(
                    EVENT_NAME_ENROLLMENT_DEACTIVATED,
                    {'course_id': original_key, 'user_id': student.id, 'mode': mode}
                ),
                call(
                    EVENT_NAME_ENROLLMENT_ACTIVATED,
                    {'course_id': new_key_one, 'user_id': student.id, 'mode': mode}
                ),
                call(
                    EVENT_NAME_ENROLLMENT_MODE_CHANGED,
                    {'course_id': new_key_one, 'user_id': student.id, 'mode': mode}
                ),
                call(
                    EVENT_NAME_ENROLLMENT_ACTIVATED,
                    {'course_id': new_key_two, 'user_id': student.id, 'mode': mode}
                ),
                call(
                    EVENT_NAME_ENROLLMENT_MODE_CHANGED,
                    {'course_id': new_key_two, 'user_id': student.id, 'mode': mode}
                )
            ]
        )
        self.mock_tracker.reset_mock()

        # Confirm the enrollment mode is verified on the new courses, and enrollment is enabled as appropriate.
        self.assertEquals((mode, False), CourseEnrollment.enrollment_mode_for_user(student, course.id))
        self.assertEquals((mode, True), CourseEnrollment.enrollment_mode_for_user(student, new_course_one.id))
        self.assertEquals((mode, True), CourseEnrollment.enrollment_mode_for_user(student, new_course_two.id))

        # Confirm the student has not be refunded.
        target_certs = CertificateItem.objects.filter(
            course_id=course.id, user_id=student, status='purchased', mode=mode
        )
        self.assertTrue(target_certs[0])
        self.assertFalse(target_certs[0].refund_requested_time)
        self.assertEquals(target_certs[0].order.status, 'purchased')

    def _create_course(self, course_location):
        """ Creates a course """
        return CourseFactory.create(
            org=course_location.org,
            number=course_location.course,
            run=course_location.run
        )

    def _create_and_purchase_verified(self, student, course_id):
        """ Creates a verified mode for the course and purchases it for the student. """
        course_mode = CourseMode(course_id=course_id,
                                 mode_slug="verified",
                                 mode_display_name="verified cert",
                                 min_price=50)
        course_mode.save()
        # When there is no expiration date on a verified mode, the user can always get a refund
        cart = Order.get_cart_for_user(user=student)
        CertificateItem.add_to_order(cart, course_id, 50, 'verified')
        cart.purchase()
