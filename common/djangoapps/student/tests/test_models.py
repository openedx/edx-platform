# pylint: disable=missing-docstring

import hashlib

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db.models.functions import Lower

from student.models import CourseEnrollment
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CourseEnrollmentTests(SharedModuleStoreTestCase):
    @classmethod
    def setUpClass(cls):
        super(CourseEnrollmentTests, cls).setUpClass()
        cls.course = CourseFactory()

    def setUp(self):
        super(CourseEnrollmentTests, self).setUp()
        self.user = UserFactory.create()
        self.user_2 = UserFactory.create()

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
        expected = hashlib.md5(self.user.username).hexdigest()
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
        expected = hashlib.md5(expected).hexdigest()
        self.assertEqual(CourseEnrollment.generate_enrollment_status_hash(self.user), expected)
        self.assert_enrollment_status_hash_cached(self.user, expected)

        # Multiple enrollments
        CourseEnrollmentFactory.create(user=self.user)
        enrollments = CourseEnrollment.enrollments_for_user(self.user).order_by(Lower('course_id'))
        hash_elements = [self.user.username]
        hash_elements += [
            '{course_id}={mode}'.format(course_id=str(enrollment.course_id).lower(), mode=enrollment.mode.lower()) for
            enrollment in enrollments]
        expected = hashlib.md5('&'.join(hash_elements)).hexdigest()
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
