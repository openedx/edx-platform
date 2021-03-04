"""
All tests for mandrill client tasks
"""
from openedx.adg.common.lib.mandrill_client import tasks as mandrill_tasks


def test_task_send_mandrill_email(mocker):
    mock_mandrill = mocker.patch.object(mandrill_tasks, 'MandrillClient')

    mandrill_tasks.task_send_mandrill_email('email_template', 'user@email.com', {'content': 'content'})

    mock_mandrill.assert_called_once_with()
