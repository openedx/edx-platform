""" Test the test_send_program_reminder_emails command line script."""


from unittest.mock import patch

import ddt
from django.core.management import call_command
from django.test.utils import override_settings
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms
from lms.djangoapps.save_for_later.tests.factories import SavedPogramFactory
from openedx.core.djangoapps.catalog.tests.factories import ProgramFactory
from lms.djangoapps.save_for_later.models import SavedProgram


@ddt.ddt
@skip_unless_lms
class SavedProgramReminderEmailsTest(SharedModuleStoreTestCase):
    """
    Test the send_program_reminder_emails management command
    """

    def setUp(self):
        super().setUp()
        self.uuid = '587f6abe-bfa4-4125-9fbe-4789bf3f97f1'
        self.program = ProgramFactory(uuid=self.uuid)
        self.saved_program = SavedPogramFactory.create(program_uuid=self.uuid)

    @override_settings(
        EDX_BRAZE_API_KEY='test-key',
        EDX_BRAZE_API_SERVER='http://test.url'
    )
    @patch('lms.djangoapps.save_for_later.management.commands.send_program_reminder_emails.get_programs')
    def test_send_reminder_emails(self, mock_get_programs):
        mock_get_programs.return_value = self.program
        with patch('lms.djangoapps.utils.BrazeClient') as mock_task:
            call_command('send_program_reminder_emails', '--batch-size=1')
            mock_task.assert_called()

        saved_program = SavedProgram.objects.filter(program_uuid=self.uuid).first()
        assert saved_program.reminder_email_sent is True
        assert saved_program.email_sent_count > 0
