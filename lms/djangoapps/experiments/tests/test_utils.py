"""
Tests of experiment functionality
"""

from datetime import timedelta
from decimal import Decimal
from django.utils.timezone import now
from unittest import TestCase

from opaque_keys.edx.keys import CourseKey
from lms.djangoapps.course_blocks.transformers.tests.helpers import ModuleStoreTestCase
from lms.djangoapps.courseware import courses
from lms.djangoapps.experiments.utils import (
    get_course_entitlement_price_and_sku,
    get_experiment_user_metadata_context,
    get_program_price_and_skus,
    get_unenrolled_courses,
    is_enrolled_in_course_run
)
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.factories import CourseFactory


class ExperimentUtilsTests(ModuleStoreTestCase, TestCase):
    """
    Tests of experiment functionality
    """

    def setUp(self):
        super(ExperimentUtilsTests, self).setUp()

        # Create a course run
        self.run_a_price = '86.00'
        self.run_a_sku = 'B9B6D0B'
        seat_a = {'type': 'verified', 'price': self.run_a_price, 'sku': self.run_a_sku}
        seats = [seat_a]
        self.course_run_a = {'status': 'published', 'seats': seats}

        # Create an entitlement
        self.entitlement_a_price = '199.23'
        self.entitlement_a_sku = 'B37EBA0'
        self.entitlement_a = {'mode': 'verified', 'price': self.entitlement_a_price, 'sku': self.entitlement_a_sku}

    def test_valid_course_run_key_enrollment(self):
        course_run = {
            'key': 'course-v1:DelftX+NGIx+RA0',
        }
        enrollment_ids = {CourseKey.from_string('course-v1:DelftX+NGIx+RA0')}
        self.assertTrue(is_enrolled_in_course_run(course_run, enrollment_ids))

    def test_invalid_course_run_key_enrollment(self):
        course_run = {
            'key': 'cr_key',
        }
        enrollment_ids = {CourseKey.from_string('course-v1:DelftX+NGIx+RA0')}
        self.assertFalse(is_enrolled_in_course_run(course_run, enrollment_ids))

    def test_program_price_and_skus_for_empty_courses(self):
        price, skus = get_program_price_and_skus([])
        self.assertEqual(None, price)
        self.assertEqual(None, skus)

    def test_unenrolled_courses_for_empty_courses(self):
        unenrolled_courses = get_unenrolled_courses([], [])
        self.assertEqual([], unenrolled_courses)

    def test_unenrolled_courses_for_single_course(self):
        course = {'key': 'UQx+ENGY1x'}
        courses_in_program = [course]
        user_enrollments = []

        unenrolled_courses = get_unenrolled_courses(courses_in_program, user_enrollments)
        expected_unenrolled_courses = [course]
        self.assertEqual(expected_unenrolled_courses, unenrolled_courses)

    def test_price_and_sku_from_empty_course(self):
        course = {}

        price, sku = get_course_entitlement_price_and_sku(course)
        self.assertEqual(None, price)
        self.assertEqual(None, sku)

    def test_price_and_sku_from_entitlement(self):
        entitlements = [self.entitlement_a]
        course = {'key': 'UQx+ENGY1x', 'entitlements': entitlements}

        price, sku = get_course_entitlement_price_and_sku(course)
        self.assertEqual(self.entitlement_a_price, price)
        self.assertEqual(self.entitlement_a_sku, sku)

    def test_price_and_sku_from_course_run(self):
        course_runs = [self.course_run_a]
        course = {'key': 'UQx+ENGY1x', 'course_runs': course_runs}

        price, sku = get_course_entitlement_price_and_sku(course)
        expected_price = Decimal(self.run_a_price)
        self.assertEqual(expected_price, price)
        self.assertEqual(self.run_a_sku, sku)

    def test_price_and_sku_from_course(self):
        entitlements = [self.entitlement_a]
        course_a = {'key': 'UQx+ENGYCAPx', 'entitlements': entitlements}
        courses = [course_a]

        price, skus = get_program_price_and_skus(courses)
        expected_price = u'$199.23'
        self.assertEqual(expected_price, price)
        self.assertEqual(1, len(skus))
        self.assertIn(self.entitlement_a_sku, skus)

    def test_price_and_sku_from_multiple_courses(self):
        entitlements = [self.entitlement_a]
        course_runs = [self.course_run_a]
        course_a = {'key': 'UQx+ENGY1x', 'course_runs': course_runs}
        course_b = {'key': 'UQx+ENGYCAPx', 'entitlements': entitlements}
        courses = [course_a, course_b]

        price, skus = get_program_price_and_skus(courses)
        expected_price = u'$285.23'
        self.assertEqual(expected_price, price)
        self.assertEqual(2, len(skus))
        self.assertIn(self.run_a_sku, skus)
        self.assertIn(self.entitlement_a_sku, skus)

    def test_get_experiment_user_metadata_context(self):
        course = CourseFactory.create(start=now() - timedelta(days=30), pacing_type="instructor_paced", course_duration=None, upgrade_price='Free',
                                      upgrade_link=None, enrollment_mode=None, audit_access_deadline=None, program_key_fields=None, schedule_start=None,
                                      enrollment_time=None, dynamic_upgrade_deadline=None, course_upgrade_deadline=None, course_key_fields={'org': 'org.0', 'course': 'course_0', 'run': 'Run_0'})
        user = UserFactory()
        context = get_experiment_user_metadata_context(course, user)
        CourseEnrollmentFactory(course_id=course.id, user=user)

        user_metadata_expected_result = {'username': user.username,
                                         'user_id': user.id,
                                         'course_id': course.id,
                                         'enrollment_mode': course.enrollment_mode,
                                         'upgrade_link': course.upgrade_link,
                                         'upgrade_price': course.upgrade_price,
                                         'audit_access_deadline': course.audit_access_deadline,
                                         'course_duration': course.course_duration,
                                         'pacing_type': course.pacing_type,
                                         'has_staff_access': False,
                                         'forum_roles': [],
                                         'partition_groups': {},
                                         'has_non_audit_enrollments': False,
                                         'program_key_fields': course.program_key_fields,
                                         'email': user.email,
                                         'schedule_start': course.schedule_start,
                                         'enrollment_time': course.enrollment_time,
                                         'course_start': course.start,
                                         'course_end': course.end,
                                         'dynamic_upgrade_deadline': course.dynamic_upgrade_deadline,
                                         'course_upgrade_deadline': course.course_upgrade_deadline,
                                         'course_key_fields': course.course_key_fields}

        user_metadata = context.get('user_metadata')

        self.assertTrue(user_metadata, user_metadata_expected_result)
