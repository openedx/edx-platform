"""
Unit tests for event bus tests for course unenrollments
"""

import unittest
from datetime import datetime, timezone
from unittest import mock
from uuid import uuid4

from django.test.utils import override_settings
from common.djangoapps.student.handlers import course_unenrollment_receiver
from common.djangoapps.student.tests.factories import (
    UserFactory,
    CourseEnrollmentFactory,
)

from openedx_events.data import EventsMetadata
from openedx_events.learning.signals import COURSE_UNENROLLMENT_COMPLETED
from pytest import mark


@mark.django_db
class UnenrollmentEventBusTests(unittest.TestCase):
    """
    Tests for unenrollment events that interact with the event bus.
    """
    @override_settings(ENABLE_SEND_ENROLLMENT_EVENTS_OVER_BUS=False)
    @mock.patch('common.djangoapps.student.handlers.get_producer', autospec=True)
    def test_event_disabled(self, mock_producer):
        """
        Test to verify that we do not push `CERTIFICATE_CREATED` events to the event bus if the
        `SEND_CERTIFICATE_CREATED_SIGNAL` setting is disabled.
        """
        course_unenrollment_receiver(None, None)
        mock_producer.assert_not_called()

    @override_settings(FEATURES={'ENABLE_SEND_ENROLLMENT_EVENTS_OVER_BUS': True})
    @mock.patch('common.djangoapps.student.handlers.get_producer', autospec=True)
    def test_event_enabled(self, mock_producer):
        """
        Test to verify that we push `COURSE_UNENROLLMENT_COMPLETED` events to the event bus.
        """
        user = UserFactory()
        enrollment = CourseEnrollmentFactory(user=user)

        event_metadata = EventsMetadata(
            event_type=COURSE_UNENROLLMENT_COMPLETED.event_type,
            id=uuid4(),
            minorversion=0,
            source='openedx/lms/web',
            sourcehost='lms.test',
            time=datetime.now(timezone.utc)
        )

        event_kwargs = {
            'enrollment': enrollment,
            'metadata': event_metadata
        }
        course_unenrollment_receiver(None, COURSE_UNENROLLMENT_COMPLETED, **event_kwargs)

        # verify that the data sent to the event bus matches what we expect
        print(mock_producer.return_value)
        print(mock_producer.return_value.send.call_args)
        data = mock_producer.return_value.send.call_args.kwargs
        assert data['event_data']['enrollment'] == enrollment
        assert data['topic'] == 'course-unenrollment-lifecycle'
        assert data['event_key_field'] == 'enrollment.course.course_key'
