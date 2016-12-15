"""
This module contains tests for programs-related signals and signal handlers.
"""

from django.test import TestCase
import mock

from student.tests.factories import UserFactory

from openedx.core.djangoapps.signals.signals import COURSE_CERT_AWARDED
from openedx.core.djangoapps.programs.signals import handle_course_cert_awarded


TEST_USERNAME = 'test-user'


@mock.patch('openedx.core.djangoapps.programs.tasks.award_program_certificates.delay')
@mock.patch(
    'openedx.core.djangoapps.programs.models.ProgramsApiConfig.is_certification_enabled',
    new_callable=mock.PropertyMock,
    return_value=False,
)
class CertAwardedReceiverTest(TestCase):
    """
    Tests for the `handle_course_cert_awarded` signal handler function.
    """

    @property
    def signal_kwargs(self):
        """
        DRY helper.
        """
        return dict(
            sender=self.__class__,
            user=UserFactory.create(username=TEST_USERNAME),
            course_key='test-course',
            mode='test-mode',
            status='test-status',
        )

    def test_signal_received(self, mock_is_certification_enabled, mock_task):  # pylint: disable=unused-argument
        """
        Ensures the receiver function is invoked when COURSE_CERT_AWARDED is
        sent.

        Suboptimal: because we cannot mock the receiver function itself (due
        to the way django signals work), we mock a configuration call that is
        known to take place inside the function.
        """
        COURSE_CERT_AWARDED.send(**self.signal_kwargs)
        self.assertEqual(mock_is_certification_enabled.call_count, 1)

    def test_programs_disabled(self, mock_is_certification_enabled, mock_task):
        """
        Ensures that the receiver function does nothing when the programs API
        configuration is not enabled.
        """
        handle_course_cert_awarded(**self.signal_kwargs)
        self.assertEqual(mock_is_certification_enabled.call_count, 1)
        self.assertEqual(mock_task.call_count, 0)

    def test_programs_enabled(self, mock_is_certification_enabled, mock_task):
        """
        Ensures that the receiver function invokes the expected celery task
        when the programs API configuration is enabled.
        """
        mock_is_certification_enabled.return_value = True
        handle_course_cert_awarded(**self.signal_kwargs)
        self.assertEqual(mock_is_certification_enabled.call_count, 1)
        self.assertEqual(mock_task.call_count, 1)
        self.assertEqual(mock_task.call_args[0], (TEST_USERNAME,))
