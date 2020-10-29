import datetime
import hashlib

import ddt
import factory
import pytz
from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache
from django.db.models import signals
from django.db.models.functions import Lower
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.courseware.models import DynamicUpgradeDeadlineConfiguration
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.schedules.models import Schedule
from openedx.core.djangoapps.schedules.tests.factories import ScheduleFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.models import (
    ALLOWEDTOENROLL_TO_ENROLLED,
    AccountRecovery,
    CourseEnrollment,
    CourseEnrollmentAllowed,
    ManualEnrollmentAudit,
    PendingEmailChange,
    PendingNameChange
)
from common.djangoapps.student.tests.factories import AccountRecoveryFactory, CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class CourseEnrollmentTests(SharedModuleStoreTestCase):
    @classmethod
    def setUpClass(cls):
        super(CourseEnrollmentTests, cls).setUpClass()
        cls.course = CourseFactory()

    def setUp(self):
        super(CourseEnrollmentTests, self).setUp()
        self.user = UserFactory()
        self.user_2 = UserFactory()

    def test_enrollment_status_hash_cache_key(self):
        username = 'test-user'
        user = UserFactory(username=username)
        expected = 'enrollment_status_hash_' + username
        self.assertEqual(CourseEnrollment.enrollment_status_hash_cache_key(user), expected)

    def assert_enrollment_status_hash_cached(self, user, expected_value):
        self.assertEqual(cache.get(CourseEnrollment.enrollment_status_hash_cache_key(user)), expected_value)

    def test_generate_enrollment_status_hash(self):
        """ Verify the method returns a hash of a user's current enrollments. """
        # Return None for anonymous users
        self.assertIsNone(CourseEnrollment.generate_enrollment_status_hash(AnonymousUser()))

        # No enrollments
        expected = hashlib.md5(self.user.username.encode('utf-8')).hexdigest()
        self.assertEqual(CourseEnrollment.generate_enrollment_status_hash(self.user), expected)
        self.assert_enrollment_status_hash_cached(self.user, expected)

        # No active enrollments
        enrollment_mode = 'verified'
        course_id = self.course.id  # pylint: disable=no-member
        enrollment = CourseEnrollmentFactory.create(user=self.user, course_id=course_id, mode=enrollment_mode,
                                                    is_active=False)
        self.assertEqual(CourseEnrollment.generate_enrollment_status_hash(self.user), expected)
        self.assert_enrollment_status_hash_cached(self.user, expected)

        # One active enrollment
        enrollment.is_active = True
        enrollment.save()
        expected = '{username}&{course_id}={mode}'.format(
            username=self.user.username, course_id=str(course_id).lower(), mode=enrollment_mode.lower()
        )
        expected = hashlib.md5(expected.encode('utf-8')).hexdigest()
        self.assertEqual(CourseEnrollment.generate_enrollment_status_hash(self.user), expected)
        self.assert_enrollment_status_hash_cached(self.user, expected)

        # Multiple enrollments
        CourseEnrollmentFactory.create(user=self.user)
        enrollments = CourseEnrollment.enrollments_for_user(self.user).order_by(Lower('course_id'))
        hash_elements = [self.user.username]
        hash_elements += [
            '{course_id}={mode}'.format(course_id=str(enrollment.course_id).lower(), mode=enrollment.mode.lower()) for
            enrollment in enrollments]
        expected = hashlib.md5('&'.join(hash_elements).encode('utf-8')).hexdigest()
        self.assertEqual(CourseEnrollment.generate_enrollment_status_hash(self.user), expected)
        self.assert_enrollment_status_hash_cached(self.user, expected)

    def test_save_deletes_cached_enrollment_status_hash(self):
        """ Verify the method deletes the cached enrollment status hash for the user. """
        # There should be no cached value for a new user with no enrollments.
        self.assertIsNone(cache.get(CourseEnrollment.enrollment_status_hash_cache_key(self.user)))

        # Generating a status hash should cache the generated value.
        status_hash = CourseEnrollment.generate_enrollment_status_hash(self.user)
        self.assert_enrollment_status_hash_cached(self.user, status_hash)

        # Modifying enrollments should delete the cached value.
        CourseEnrollmentFactory.create(user=self.user)
        self.assertIsNone(cache.get(CourseEnrollment.enrollment_status_hash_cache_key(self.user)))

    def test_users_enrolled_in_active_only(self):
        """CourseEnrollment.users_enrolled_in should return only Users with active enrollments when
        `include_inactive` has its default value (False)."""
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)
        CourseEnrollmentFactory.create(user=self.user_2, course_id=self.course.id, is_active=False)

        active_enrolled_users = list(CourseEnrollment.objects.users_enrolled_in(self.course.id))
        self.assertEqual([self.user], active_enrolled_users)

    def test_users_enrolled_in_all(self):
        """CourseEnrollment.users_enrolled_in should return active and inactive users when
        `include_inactive` is True."""
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, is_active=True)
        CourseEnrollmentFactory.create(user=self.user_2, course_id=self.course.id, is_active=False)

        all_enrolled_users = list(
            CourseEnrollment.objects.users_enrolled_in(self.course.id, include_inactive=True)
        )
        self.assertListEqual([self.user, self.user_2], all_enrolled_users)

    @skip_unless_lms
    # NOTE: We mute the post_save signal to prevent Schedules from being created for new enrollments
    @factory.django.mute_signals(signals.post_save)
    def test_upgrade_deadline(self):
        """ The property should use either the CourseMode or related Schedule to determine the deadline. """
        course = CourseFactory(self_paced=True)
        course_mode = CourseModeFactory(
            course_id=course.id,
            mode_slug=CourseMode.VERIFIED,
            # This must be in the future to ensure it is returned by downstream code.
            expiration_datetime=datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=1)
        )
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        self.assertEqual(Schedule.objects.all().count(), 0)
        self.assertEqual(enrollment.upgrade_deadline, course_mode.expiration_datetime)

    @skip_unless_lms
    # NOTE: We mute the post_save signal to prevent Schedules from being created for new enrollments
    @factory.django.mute_signals(signals.post_save)
    def test_upgrade_deadline_with_schedule(self):
        """ The property should use either the CourseMode or related Schedule to determine the deadline. """
        course = CourseFactory(self_paced=True)
        CourseModeFactory(
            course_id=course.id,
            mode_slug=CourseMode.VERIFIED,
            # This must be in the future to ensure it is returned by downstream code.
            expiration_datetime=datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=30),
        )
        course_overview = CourseOverview.load_from_module_store(course.id)
        enrollment = CourseEnrollmentFactory(
            course_id=course.id,
            mode=CourseMode.AUDIT,
            course=course_overview,
        )

        # The schedule's upgrade deadline should be used if a schedule exists
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        schedule = ScheduleFactory(enrollment=enrollment)
        self.assertEqual(enrollment.upgrade_deadline, schedule.upgrade_deadline)

    @skip_unless_lms
    @ddt.data(*(set(CourseMode.ALL_MODES) - set(CourseMode.AUDIT_MODES)))
    def test_upgrade_deadline_for_non_upgradeable_enrollment(self, mode):
        """ The property should return None if an upgrade cannot be upgraded. """
        enrollment = CourseEnrollmentFactory(course_id=self.course.id, mode=mode)
        self.assertIsNone(enrollment.upgrade_deadline)

    @skip_unless_lms
    def test_upgrade_deadline_instructor_paced(self):
        course = CourseFactory(self_paced=False)
        course_upgrade_deadline = datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=1)
        CourseModeFactory(
            course_id=course.id,
            mode_slug=CourseMode.VERIFIED,
            # This must be in the future to ensure it is returned by downstream code.
            expiration_datetime=course_upgrade_deadline
        )
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        ScheduleFactory(enrollment=enrollment)
        self.assertIsNotNone(enrollment.schedule)
        self.assertEqual(enrollment.upgrade_deadline, course_upgrade_deadline)

    @skip_unless_lms
    def test_upgrade_deadline_with_schedule_and_professional_mode(self):
        """
        Deadline should be None for courses with professional mode.

        Regression test for EDUCATOR-2419.
        """
        course = CourseFactory(self_paced=True)
        CourseModeFactory(
            course_id=course.id,
            mode_slug=CourseMode.PROFESSIONAL,
        )
        enrollment = CourseEnrollmentFactory(course_id=course.id, mode=CourseMode.AUDIT)
        DynamicUpgradeDeadlineConfiguration.objects.create(enabled=True)
        ScheduleFactory(enrollment=enrollment)
        self.assertIsNotNone(enrollment.schedule)
        self.assertIsNone(enrollment.upgrade_deadline)

    @skip_unless_lms
    # NOTE: We mute the post_save signal to prevent Schedules from being created for new enrollments
    @factory.django.mute_signals(signals.post_save)
    def test_enrollments_not_deleted(self):
        """ Recreating a CourseOverview with an outdated version should not delete the associated enrollment. """
        course = CourseFactory(self_paced=True)
        CourseModeFactory(
            course_id=course.id,
            mode_slug=CourseMode.VERIFIED,
            # This must be in the future to ensure it is returned by downstream code.
            expiration_datetime=datetime.datetime.now(pytz.UTC) + datetime.timedelta(days=30),
        )

        # Create a CourseOverview with an outdated version
        course_overview = CourseOverview.load_from_module_store(course.id)
        course_overview.version = CourseOverview.VERSION - 1
        course_overview.save()

        # Create an inactive enrollment with this course overview
        enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=course.id,
            mode=CourseMode.AUDIT,
            course=course_overview,
        )

        # Re-fetch the CourseOverview record.
        # As a side effect, this will recreate the record, and update the version.
        course_overview_new = CourseOverview.get_from_id(course.id)
        self.assertEqual(course_overview_new.version, CourseOverview.VERSION)

        # Ensure that the enrollment record was unchanged during this re-creation
        enrollment_refetched = CourseEnrollment.objects.filter(id=enrollment.id)
        self.assertTrue(enrollment_refetched.exists())
        self.assertEqual(enrollment_refetched.all()[0], enrollment)


class PendingNameChangeTests(SharedModuleStoreTestCase):
    """
    Tests the deletion of PendingNameChange records
    """
    @classmethod
    def setUpClass(cls):
        super(PendingNameChangeTests, cls).setUpClass()
        cls.user = UserFactory()
        cls.user2 = UserFactory()

    def setUp(self):
        self.name_change, _ = PendingNameChange.objects.get_or_create(
            user=self.user,
            new_name='New Name PII',
            rationale='for testing!'
        )
        self.assertEqual(1, len(PendingNameChange.objects.all()))

    def test_delete_by_user_removes_pending_name_change(self):
        record_was_deleted = PendingNameChange.delete_by_user_value(self.user, field='user')
        self.assertTrue(record_was_deleted)
        self.assertEqual(0, len(PendingNameChange.objects.all()))

    def test_delete_by_user_no_effect_for_user_with_no_name_change(self):
        record_was_deleted = PendingNameChange.delete_by_user_value(self.user2, field='user')
        self.assertFalse(record_was_deleted)
        self.assertEqual(1, len(PendingNameChange.objects.all()))


class PendingEmailChangeTests(SharedModuleStoreTestCase):
    """
    Tests the deletion of PendingEmailChange records.
    """
    @classmethod
    def setUpClass(cls):
        super(PendingEmailChangeTests, cls).setUpClass()
        cls.user = UserFactory()
        cls.user2 = UserFactory()

    def setUp(self):
        self.email_change, _ = PendingEmailChange.objects.get_or_create(
            user=self.user,
            new_email='new@example.com',
            activation_key='a' * 32
        )

    def test_delete_by_user_removes_pending_email_change(self):
        record_was_deleted = PendingEmailChange.delete_by_user_value(self.user, field='user')
        self.assertTrue(record_was_deleted)
        self.assertEqual(0, len(PendingEmailChange.objects.all()))

    def test_delete_by_user_no_effect_for_user_with_no_email_change(self):
        record_was_deleted = PendingEmailChange.delete_by_user_value(self.user2, field='user')
        self.assertFalse(record_was_deleted)
        self.assertEqual(1, len(PendingEmailChange.objects.all()))


class TestCourseEnrollmentAllowed(TestCase):

    def setUp(self):
        super(TestCourseEnrollmentAllowed, self).setUp()
        self.email = 'learner@example.com'
        self.course_key = CourseKey.from_string("course-v1:edX+DemoX+Demo_Course")
        self.user = UserFactory.create()
        self.allowed_enrollment = CourseEnrollmentAllowed.objects.create(
            email=self.email,
            course_id=self.course_key,
            user=self.user
        )

    def test_retiring_user_deletes_record(self):
        is_successful = CourseEnrollmentAllowed.delete_by_user_value(
            value=self.email,
            field='email'
        )
        self.assertTrue(is_successful)
        user_search_results = CourseEnrollmentAllowed.objects.filter(
            email=self.email
        )
        self.assertFalse(user_search_results)

    def test_retiring_nonexistent_user_doesnt_modify_records(self):
        is_successful = CourseEnrollmentAllowed.delete_by_user_value(
            value='nonexistentlearner@example.com',
            field='email'
        )
        self.assertFalse(is_successful)
        user_search_results = CourseEnrollmentAllowed.objects.filter(
            email=self.email
        )
        self.assertTrue(user_search_results.exists())


class TestManualEnrollmentAudit(SharedModuleStoreTestCase):
    """
    Tests for the ManualEnrollmentAudit model.
    """
    @classmethod
    def setUpClass(cls):
        super(TestManualEnrollmentAudit, cls).setUpClass()
        cls.course = CourseFactory()
        cls.other_course = CourseFactory()
        cls.user = UserFactory()
        cls.instructor = UserFactory(username='staff', is_staff=True)

    def test_retirement(self):
        """
        Tests that calling the retirement method for a specific enrollment retires
        the enrolled_email and reason columns of each row associated with that
        enrollment.
        """
        enrollment = CourseEnrollment.enroll(self.user, self.course.id)
        other_enrollment = CourseEnrollment.enroll(self.user, self.other_course.id)
        ManualEnrollmentAudit.create_manual_enrollment_audit(
            self.instructor, self.user.email, ALLOWEDTOENROLL_TO_ENROLLED,
            'manually enrolling unenrolled user', enrollment
        )
        ManualEnrollmentAudit.create_manual_enrollment_audit(
            self.instructor, self.user.email, ALLOWEDTOENROLL_TO_ENROLLED,
            'manually enrolling unenrolled user again', enrollment
        )
        ManualEnrollmentAudit.create_manual_enrollment_audit(
            self.instructor, self.user.email, ALLOWEDTOENROLL_TO_ENROLLED,
            'manually enrolling unenrolled user', other_enrollment
        )
        ManualEnrollmentAudit.create_manual_enrollment_audit(
            self.instructor, self.user.email, ALLOWEDTOENROLL_TO_ENROLLED,
            'manually enrolling unenrolled user again', other_enrollment
        )
        self.assertTrue(ManualEnrollmentAudit.objects.filter(enrollment=enrollment).exists())
        # retire the ManualEnrollmentAudit objects associated with the above enrollments
        ManualEnrollmentAudit.retire_manual_enrollments(user=self.user, retired_email="xxx")
        self.assertTrue(ManualEnrollmentAudit.objects.filter(enrollment=enrollment).exists())
        self.assertFalse(ManualEnrollmentAudit.objects.filter(enrollment=enrollment).exclude(
            enrolled_email="xxx"
        ))
        self.assertFalse(ManualEnrollmentAudit.objects.filter(enrollment=enrollment).exclude(
            reason=""
        ))


class TestAccountRecovery(TestCase):
    """
    Tests for the AccountRecovery Model
    """

    def test_retire_recovery_email(self):
        """
        Assert that Account Record for a given user is deleted when `retire_recovery_email` is called
        """
        # Create user and associated recovery email record
        user = UserFactory()
        AccountRecoveryFactory(user=user)
        assert len(AccountRecovery.objects.filter(user_id=user.id)) == 1

        # Retire recovery email
        AccountRecovery.retire_recovery_email(user_id=user.id)

        # Assert that there is no longer an AccountRecovery record for this user
        assert len(AccountRecovery.objects.filter(user_id=user.id)) == 0


@ddt.ddt
class TestUserPostSaveCallback(SharedModuleStoreTestCase):
    """
    Tests for the user post save callback.
    These tests are to ensure that user activation auto-enrolls invited users into courses without
    changing any existing course mode states.
    """
    def setUp(self):
        super(TestUserPostSaveCallback, self).setUp()
        self.course = CourseFactory.create()

    @ddt.data(*(set(CourseMode.ALL_MODES) - set(CourseMode.AUDIT_MODES)))
    def test_paid_user_not_downgraded_on_activation(self, mode):
        """
        Make sure that students who are already enrolled + have paid do not get downgraded to audit mode
        when their account is activated.
        """
        # fixture
        student = self._set_up_invited_student(
            course=self.course,
            active=False,
            course_mode=mode
        )

        # trigger the post_save callback
        student.is_active = True
        student.save()

        # reload values from the database + make sure they are in the expected state
        actual_course_enrollment = CourseEnrollment.objects.get(user=student, course_id=self.course.id)
        actual_student = User.objects.get(email=student.email)
        actual_cea = CourseEnrollmentAllowed.objects.get(email=student.email)

        self.assertEqual(actual_course_enrollment.mode, mode)
        self.assertEqual(actual_student.is_active, True)
        self.assertEqual(actual_cea.user, student)

    def test_not_enrolled_student_is_enrolled(self):
        """
        Make sure that invited students who are not enrolled become enrolled when their account is activated.
        They should be enrolled in the course in audit mode.
        """
        # fixture
        student = self._set_up_invited_student(
            course=self.course,
            active=False,
            enrolled=False
        )

        # trigger the post_save callback
        student.is_active = True
        student.save()

        # reload values from the database + make sure they are in the expected state
        actual_course_enrollment = CourseEnrollment.objects.get(user=student, course_id=self.course.id)
        actual_student = User.objects.get(email=student.email)
        actual_cea = CourseEnrollmentAllowed.objects.get(email=student.email)

        self.assertEqual(actual_course_enrollment.mode, u"audit")
        self.assertEqual(actual_student.is_active, True)
        self.assertEqual(actual_cea.user, student)

    def test_verified_student_not_downgraded_when_changing_email(self):
        """
        Make sure that verified students do not get downgrade if they are active + changing their email.
        """
        # fixture
        student = self._set_up_invited_student(
            course=self.course,
            active=True,
            course_mode=u'verified'
        )
        old_email = student.email

        # trigger the post_save callback
        student.email = "foobar" + old_email
        student.save()

        # reload values from the database + make sure they are in the expected state
        actual_course_enrollment = CourseEnrollment.objects.get(user=student, course_id=self.course.id)
        actual_student = User.objects.get(email=student.email)

        self.assertEqual(actual_course_enrollment.mode, u"verified")
        self.assertEqual(actual_student.is_active, True)

    def _set_up_invited_student(self, course, active=False, enrolled=True, course_mode=''):
        """
        Helper function to create a user in the right state, invite them into the course, and update their
        course mode if needed.
        """
        email = 'robot@robot.org'
        user = UserFactory(
            username='somestudent',
            first_name='Student',
            last_name='Person',
            email=email,
            is_active=active
        )

        # invite the user to the course
        cea = CourseEnrollmentAllowed(email=email, course_id=course.id, auto_enroll=True)
        cea.save()

        if enrolled:
            CourseEnrollment.enroll(user, course.id)

            if course_mode:
                course_enrollment = CourseEnrollment.objects.get(
                    user=user, course_id=self.course.id
                )
                course_enrollment.mode = course_mode
                course_enrollment.save()

        return user
