"""
All tests for mandrill client tasks
"""
from unittest.mock import patch

from openedx.adg.common.lib.mandrill_client.tasks import task_send_mandrill_email


@patch('openedx.adg.common.lib.mandrill_client.tasks.MandrillClient')
def test_task_send_mandrill_email(mock_mandrill_client):
    task_send_mandrill_email('email_template', 'user@email.com', {'content': 'content'})

    mock_mandrill_client.assert_called_once()
