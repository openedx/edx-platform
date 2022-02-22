"""
Unit tests for the signals
"""
from uuid import uuid4
from django.test import TestCase

from common.djangoapps.student.tests.factories import UserFactory
from ..models import SavedCourse, SavedProgram
from ..signals import _listen_for_lms_retire


class RetirementSignalTest(TestCase):
    """
    Tests for the user retirement signal
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.email = self.user.email

    def _create_objects(self):
        """
        Create test objects.
        """
        SavedCourse.objects.create(user_id=self.user.id, email=self.email, course_id='course-v1:TestX+TestX101+1T2022')
        SavedProgram.objects.create(user_id=self.user.id, email=self.email, program_uuid=uuid4())

        assert SavedCourse.objects.filter(email=self.email).exists()
        assert SavedProgram.objects.filter(email=self.email).exists()

    def test_retire_success(self):
        self._create_objects()
        _listen_for_lms_retire(sender=self.__class__, user=self.user, email=self.email)

        assert not SavedCourse.objects.filter(email=self.email).exists()
        assert not SavedProgram.objects.filter(email=self.email).exists()

    def test_retire_success_no_entries(self):
        assert not SavedCourse.objects.filter(email=self.email).exists()
        assert not SavedProgram.objects.filter(email=self.email).exists()
        _listen_for_lms_retire(sender=self.__class__, user=self.user, email=self.email)
