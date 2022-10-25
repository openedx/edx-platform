"""
Tests for the Agreements API
"""
import logging

from testfixtures import LogCapture

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.agreements.api import (
    create_integrity_signature,
    get_integrity_signature,
    get_integrity_signatures_for_course,
)
from openedx.core.djangolib.testing.utils import skip_unless_lms
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order

LOGGER_NAME = "openedx.core.djangoapps.agreements.api"


@skip_unless_lms
class TestIntegritySignatureApi(SharedModuleStoreTestCase):
    """
    Tests for the integrity signature API
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = UserFactory()
        cls.course = CourseFactory()
        cls.course_id = str(cls.course.id)

    def test_create_integrity_signature(self):
        """
        Test to create an integrity signature
        """
        signature = create_integrity_signature(self.user.username, self.course_id)
        self._assert_integrity_signature(signature)

    def test_create_duplicate_integrity_signature(self):
        """
        Test that duplicate integrity signatures cannot be created
        """
        with LogCapture(LOGGER_NAME, level=logging.WARNING) as logger:
            create_integrity_signature(self.user.username, self.course_id)
            create_integrity_signature(self.user.username, self.course_id)
            signature = get_integrity_signature(self.user.username, self.course_id)
            self._assert_integrity_signature(signature)
            logger.check((
                LOGGER_NAME,
                'WARNING',
                (
                    'Integrity signature already exists for user_id={user_id} and '
                    'course_id={course_id}'.format(
                        user_id=self.user.id, course_id=str(self.course_id)
                    )
                )
            ))

    def test_get_integrity_signature(self):
        """
        Test to get an integrity signature
        """
        create_integrity_signature(self.user.username, self.course_id)
        signature = get_integrity_signature(self.user.username, self.course_id)
        self._assert_integrity_signature(signature)

    def test_get_nonexistent_integrity_signature(self):
        """
        Test that None is returned if an integrity signature does not exist
        """
        signature = get_integrity_signature(self.user.username, self.course_id)
        self.assertIsNone(signature)

    def test_get_integrity_signatures_for_course(self):
        """
        Test to get all integrity signatures for a course
        """
        create_integrity_signature(self.user.username, self.course_id)
        second_user = UserFactory()
        create_integrity_signature(second_user.username, self.course_id)
        signatures = get_integrity_signatures_for_course(self.course_id)
        self._assert_integrity_signature(signatures[0])
        self.assertEqual(signatures[1].user, second_user)
        self.assertEqual(signatures[1].course_key, self.course.id)

    def test_get_integrity_signatures_for_course_empty(self):
        """
        Test that a course with no integrity signatures returns an empty queryset
        """
        signatures = get_integrity_signatures_for_course(self.course_id)
        self.assertEqual(len(signatures), 0)

    def _assert_integrity_signature(self, signature):
        """
        Helper function to assert the returned integrity signature has the correct
        user and course key
        """
        self.assertEqual(signature.user, self.user)
        self.assertEqual(signature.course_key, self.course.id)
