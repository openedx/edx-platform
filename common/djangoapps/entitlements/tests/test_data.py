"""
Test the Data Aggregation Layer for Course Entitlements.
"""
import unittest
import uuid

import ddt
from django.conf import settings

from entitlements.models import CourseEntitlement
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import CourseEnrollmentFactory


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EntitlementDataTest(ModuleStoreTestCase):
    """
    Test course entitlement data aggregation.
    """
    USERNAME = "Bob"
    EMAIL = "bob@example.com"
    PASSWORD = "edx"

    def setUp(self):
        """Create a course and user, then log in. """
        super(EntitlementDataTest, self).setUp()
        self.course = CourseFactory.create()
        self.course_uuid = uuid.uuid4()
        self.user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

    def _add_entitlement_for_user(self, course, user, parent_uuid):
        entitlement_data = {
            'user': user,
            'course_uuid': parent_uuid,
            'mode': 'verified',
        }
        stored_entitlement, is_created = CourseEntitlement.update_or_create_new_entitlement(
            user,
            parent_uuid,
            entitlement_data
        )
        return stored_entitlement, is_created

    def test_get_entitlement_info(self):
        stored_entitlement, is_created = self._add_entitlement_for_user(self.course, self.user, self.course_uuid)
        self.assertTrue(is_created)

        # Get the Entitlement and verify the data
        entitlement = CourseEntitlement.get_user_course_entitlement(self.user, self.course_uuid)
        self.assertEqual(entitlement.course_uuid, self.course_uuid)
        self.assertEqual(entitlement.mode, 'verified')
        self.assertIsNone(entitlement.enrollment_course_run)

    def test_get_course_entitlements(self):
        course2 = CourseFactory.create()

        stored_entitlement, is_created = self._add_entitlement_for_user(self.course, self.user, self.course_uuid)
        self.assertTrue(is_created)

        course2_uuid = uuid.uuid4()
        stored_entitlement2, is_created2 = self._add_entitlement_for_user(course2, self.user, course2_uuid)
        self.assertTrue(is_created2)

        # Get the Entitlement and verify the data
        entitlement_list = CourseEntitlement.entitlements_for_user(self.user)

        self.assertEqual(2, len(entitlement_list))
        self.assertEqual(self.course_uuid, entitlement_list[0].course_uuid)
        self.assertEqual(course2_uuid, entitlement_list[1].course_uuid)

    def test_set_enrollment(self):
        stored_entitlement, is_created = self._add_entitlement_for_user(self.course, self.user, self.course_uuid)
        self.assertTrue(is_created)

        # Entitlement set not enroll the user in the Course run
        enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course.id,
            mode="verified",
        )
        CourseEntitlement.update_entitlement_enrollment(self.user, self.course_uuid, enrollment)

        entitlement = CourseEntitlement.get_user_course_entitlement(self.user, self.course_uuid)
        self.assertIsNotNone(entitlement.enrollment_course_run)

    def test_remove_enrollment(self):
        stored_entitlement, is_created = self._add_entitlement_for_user(self.course, self.user, self.course_uuid)
        self.assertTrue(is_created)

        # Entitlement set not enroll the user in the Course run
        enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course.id,
            mode="verified",
        )
        CourseEntitlement.update_entitlement_enrollment(self.user, self.course_uuid, enrollment)

        entitlement = CourseEntitlement.get_user_course_entitlement(self.user, self.course_uuid)
        self.assertIsNotNone(entitlement.enrollment_course_run)

        CourseEntitlement.update_entitlement_enrollment(self.user, self.course_uuid, None)
        entitlement = CourseEntitlement.get_user_course_entitlement(self.user, self.course_uuid)
        self.assertIsNone(entitlement.enrollment_course_run)
