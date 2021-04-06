"""
All tests for mandrill client tasks
"""
from unittest.mock import patch

import pytest

from openedx.adg.common.lib.mandrill_client.tasks import task_send_mandrill_email


@pytest.mark.django_db
@patch('openedx.adg.common.lib.mandrill_client.tasks.MandrillClient')
@pytest.mark.parametrize(
    'email_addresses', [['user1@email.com'], ['user1@email.com', 'user2@email.com']]
)
def test_task_send_mandrill_email(mock_mandrill_client, email_addresses):
    task_send_mandrill_email('email_template', email_addresses, {'content': 'content'})
    mock_mandrill_client.assert_called_once()
