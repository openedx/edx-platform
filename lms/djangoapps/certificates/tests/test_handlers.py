"""
Unit tests for certificates signals
"""
from datetime import datetime, timezone
from unittest import mock
from uuid import uuid4

from django.test import TestCase
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx_events.data import EventsMetadata
from openedx_events.learning.data import ExamAttemptData, UserData, UserPersonalData
from openedx_events.learning.signals import EXAM_ATTEMPT_REJECTED

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.certificates.handlers import handle_exam_attempt_rejected_event


class ExamCompletionEventBusTests(TestCase):
    """
    Tests completion events from the event bus.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_key = CourseKey.from_string('course-v1:edX+TestX+Test_Course')
        cls.subsection_id = 'block-v1:edX+TestX+Test_Course+type@sequential+block@subsection'
        cls.usage_key = UsageKey.from_string(cls.subsection_id)
        cls.student_user = UserFactory(
            username='student_user',
        )

    @staticmethod
    def _get_exam_event_data(student_user, course_key, usage_key, exam_type, requesting_user=None):
        """ create ExamAttemptData object for exam based event """
        if requesting_user:
            requesting_user_data = UserData(
                id=requesting_user.id,
                is_active=True,
                pii=None
            )
        else:
            requesting_user_data = None

        return ExamAttemptData(
            student_user=UserData(
                id=student_user.id,
                is_active=True,
                pii=UserPersonalData(
                    username=student_user.username,
                    email=student_user.email,
                ),
            ),
            course_key=course_key,
            usage_key=usage_key,
            requesting_user=requesting_user_data,
            exam_type=exam_type,
        )

    @staticmethod
    def _get_exam_event_metadata(event_signal):
        """ create metadata object for event """
        return EventsMetadata(
            event_type=event_signal.event_type,
            id=uuid4(),
            minorversion=0,
            source='openedx/lms/web',
            sourcehost='lms.test',
            time=datetime.now(timezone.utc)
        )

    @mock.patch('lms.djangoapps.certificates.handlers.invalidate_certificate')
    def test_exam_attempt_rejected_event(self, mock_api_function):
        """
        Assert that CertificateService api's invalidate_certificate is called upon consuming the event
        """
        exam_event_data = self._get_exam_event_data(self.student_user,
                                                    self.course_key,
                                                    self.usage_key,
                                                    exam_type='proctored')
        event_metadata = self._get_exam_event_metadata(EXAM_ATTEMPT_REJECTED)

        event_kwargs = {
            'exam_attempt': exam_event_data,
            'metadata': event_metadata
        }
        handle_exam_attempt_rejected_event(None, EXAM_ATTEMPT_REJECTED, **event_kwargs)
        mock_api_function.assert_called_once_with(self.student_user.id, self.course_key, source='exam_event')
