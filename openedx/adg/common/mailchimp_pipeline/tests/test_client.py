"""
All tests for Mailchimp client
"""
import pytest

from openedx.adg.common.mailchimp_pipeline.client import MailchimpClient


@pytest.fixture
def mock_mailchimp_client(request, mocker):
    """
    A fixture to create patched MailChimp client for tests. This client does not need API key or list id. This fixture
    can add new mocked methods and attributes into client, through params.
    """
    mock = mocker.MagicMock()
    mock.function.return_value = request.param

    mock_mailchimp = mocker.patch('openedx.adg.common.mailchimp_pipeline.client.MailChimp')
    mock_mailchimp.return_value = mock

    return mock_mailchimp


@pytest.mark.parametrize('mock_mailchimp_client', ['lists.members.create_or_update()', ], indirect=True)
def test_create_or_update_list_member(mock_mailchimp_client, mocker):  # pylint: disable=redefined-outer-name, unused-argument
    """
    Assert that Mailchimp api function called with valid data
    """
    user_data = {'test': 'example'}

    # Mock MailChimp lists to validate call data
    mailchimp_client = MailchimpClient()
    # pylint: disable=protected-access
    mock_mailchimp_client_lists = mocker.patch.object(mailchimp_client._client, 'lists')

    mailchimp_client.create_or_update_list_member('test@example.com', user_data)

    mock_mailchimp_client_lists.members.create_or_update.assert_called_once_with(
        list_id=mocker.ANY, subscriber_hash=mocker.ANY, data=user_data
    )
