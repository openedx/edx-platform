"""
Test the Data Aggregation Layer for Course Enrollments.

"""
import ddt
from nose.tools import raises
import unittest

from django.test.utils import override_settings
from django.conf import settings
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseModeFactory
from student.models import CourseEnrollment, NonExistentCourseError
from enrollment import data

# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@ddt.ddt
@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EnrollmentDataTest(ModuleStoreTestCase):
    """
    Test course enrollment data aggregation.

    """
    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    def setUp(self):
        """Create a course and user, then log in. """
        super(EnrollmentDataTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    @ddt.data(
        # Default (no course modes in the database)
        # Expect that users are automatically enrolled as "honor".
        ([], 'honor'),

        # Audit / Verified / Honor
        # We should always go to the "choose your course" page.
        # We should also be enrolled as "honor" by default.
        (['honor', 'verified', 'audit'], 'honor'),
    )
    @ddt.unpack
    def test_enroll(self, course_modes, enrollment_mode):
        # Create the course modes (if any) required for this test case
        self._create_course_modes(course_modes)

        enrollment = data.update_course_enrollment(
            self.user.username,
            unicode(self.course.id),
            mode=enrollment_mode,
            is_active=True
        )

        self.assertTrue(CourseEnrollment.is_enrolled(self.user, self.course.id))
        course_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        self.assertTrue(is_active)
        self.assertEqual(course_mode, enrollment_mode)

        # Confirm the returned enrollment and the data match up.
        self.assertEqual(course_mode, enrollment['mode'])
        self.assertEqual(is_active, enrollment['is_active'])

    def test_unenroll(self):
        # Enroll the student in the course
        CourseEnrollment.enroll(self.user, self.course.id, mode="honor")

        enrollment = data.update_course_enrollment(
            self.user.username,
            unicode(self.course.id),
            is_active=False
        )

        # Determine that the returned enrollment is inactive.
        self.assertFalse(enrollment['is_active'])

        # Expect that we're no longer enrolled
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    @ddt.data(
        # No course modes, no course enrollments.
        ([]),

        # Audit / Verified / Honor course modes, with three course enrollments.
        (['honor', 'verified', 'audit']),
    )
    def test_get_course_info(self, course_modes):
        self._create_course_modes(course_modes, course=self.course)
        result_course = data.get_course_enrollment_info(unicode(self.course.id))
        result_slugs = [mode['slug'] for mode in result_course['course_modes']]
        for course_mode in course_modes:
            self.assertIn(course_mode, result_slugs)

    @ddt.data(
        # No course modes, no course enrollments.
        ([], []),

        # Audit / Verified / Honor course modes, with three course enrollments.
        (['honor', 'verified', 'audit'], ['1', '2', '3']),
    )
    @ddt.unpack
    def test_get_course_enrollments(self, course_modes, course_numbers):
        # Create all the courses
        created_courses = []
        for course_number in course_numbers:
            created_courses.append(CourseFactory.create(number=course_number))

        created_enrollments = []
        for course in created_courses:
            self._create_course_modes(course_modes, course=course)
            # Create the original enrollment.
            created_enrollments.append(data.update_course_enrollment(
                self.user.username,
                unicode(course.id),
            ))

        # Compare the created enrollments with the results
        # from the get enrollments request.
        results = data.get_course_enrollments(self.user.username)
        self.assertEqual(results, created_enrollments)

    @ddt.data(
        # Default (no course modes in the database)
        # Expect that users are automatically enrolled as "honor".
        ([], 'honor'),

        # Audit / Verified / Honor
        # We should always go to the "choose your course" page.
        # We should also be enrolled as "honor" by default.
        (['honor', 'verified', 'audit'], 'verified'),
    )
    @ddt.unpack
    def test_get_course_enrollment(self, course_modes, enrollment_mode):
        self._create_course_modes(course_modes)

        # Try to get an enrollment before it exists.
        result = data.get_course_enrollment(self.user.username, unicode(self.course.id))
        self.assertIsNone(result)

        # Create the original enrollment.
        enrollment = data.update_course_enrollment(
            self.user.username,
            unicode(self.course.id),
            mode=enrollment_mode,
            is_active=True
        )
        # Get the enrollment and compare it to the original.
        result = data.get_course_enrollment(self.user.username, unicode(self.course.id))
        self.assertEqual(enrollment, result)

    @raises(NonExistentCourseError)
    def test_non_existent_course(self):
        data.get_course_enrollment_info("this/is/bananas")

    def _create_course_modes(self, course_modes, course=None):
        """Create the course modes required for a test. """
        course_id = course.id if course else self.course.id
        for mode_slug in course_modes:
            CourseModeFactory.create(
                course_id=course_id,
                mode_slug=mode_slug,
                mode_display_name=mode_slug,
            )
