"""
Test the retire_one_learner.py script
"""
<<<<<<< HEAD

from click.testing import CliRunner
from mock import DEFAULT, patch
=======
from unittest.mock import DEFAULT, patch

from click.testing import CliRunner
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

from scripts.user_retirement.retire_one_learner import (
    END_STATES,
    ERR_BAD_CONFIG,
    ERR_BAD_LEARNER,
    ERR_SETUP_FAILED,
    ERR_UNKNOWN_STATE,
    ERR_USER_AT_END_STATE,
    ERR_USER_IN_WORKING_STATE,
    retire_learner
)
from scripts.user_retirement.tests.retirement_helpers import fake_config_file, get_fake_user_retirement
from scripts.user_retirement.utils.exception import HttpDoesNotExistException


def _call_script(username, fetch_ecom_segment_id=False):
    """
    Call the retired learner script with the given username and a generic, temporary config file.
    Returns the CliRunner.invoke results
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test_config.yml', 'w') as f:
            fake_config_file(f, fetch_ecom_segment_id=fetch_ecom_segment_id)
        result = runner.invoke(retire_learner, args=['--username', username, '--config_file', 'test_config.yml'])
    print(result)
    print(result.output)
    return result


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch('scripts.user_retirement.utils.edx_api.EcommerceApi.get_tracking_key')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT,
    retirement_retire_forum=DEFAULT,
    retirement_retire_mailings=DEFAULT,
    retirement_unenroll=DEFAULT,
    retirement_lms_retire=DEFAULT
)
def test_successful_retirement(*args, **kwargs):
    username = 'test_username'

    mock_get_access_token = args[1]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']
    mock_update_learner_state = kwargs['update_learner_retirement_state']
    mock_retire_forum = kwargs['retirement_retire_forum']
    mock_retire_mailings = kwargs['retirement_retire_mailings']
    mock_unenroll = kwargs['retirement_unenroll']
    mock_lms_retire = kwargs['retirement_lms_retire']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)
    mock_get_retirement_state.return_value = get_fake_user_retirement(original_username=username)

    result = _call_script(username, fetch_ecom_segment_id=True)

    # Called once per API we instantiate (LMS, ECommerce, Credentials)
    assert mock_get_access_token.call_count == 3
    mock_get_retirement_state.assert_called_once_with(username)
    assert mock_update_learner_state.call_count == 9

    # Called once per retirement
    for mock_call in (
        mock_retire_forum,
        mock_retire_mailings,
        mock_unenroll,
        mock_lms_retire
    ):
        mock_call.assert_called_once_with(mock_get_retirement_state.return_value)

    assert result.exit_code == 0
    assert 'Retirement complete' in result.output


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT
)
def test_user_does_not_exist(*args, **kwargs):
    username = 'test_username'

    mock_get_access_token = args[0]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']
    mock_update_learner_state = kwargs['update_learner_retirement_state']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)
    mock_get_retirement_state.side_effect = Exception

    result = _call_script(username)

    assert mock_get_access_token.call_count == 3
    mock_get_retirement_state.assert_called_once_with(username)
    mock_update_learner_state.assert_not_called()

    assert result.exit_code == ERR_SETUP_FAILED
    assert 'Exception' in result.output


def test_bad_config():
    username = 'test_username'
    runner = CliRunner()
    result = runner.invoke(retire_learner, args=['--username', username, '--config_file', 'does_not_exist.yml'])
    assert result.exit_code == ERR_BAD_CONFIG
    assert 'does_not_exist.yml' in result.output


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT
)
def test_bad_learner(*args, **kwargs):
    username = 'test_username'

    mock_get_access_token = args[0]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']
    mock_update_learner_state = kwargs['update_learner_retirement_state']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)

    # Broken API call, no state returned
    mock_get_retirement_state.side_effect = HttpDoesNotExistException
    result = _call_script(username)

    assert mock_get_access_token.call_count == 3
    mock_get_retirement_state.assert_called_once_with(username)
    mock_update_learner_state.assert_not_called()

    assert result.exit_code == ERR_BAD_LEARNER


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT
)
def test_user_in_working_state(*args, **kwargs):
    username = 'test_username'

    mock_get_access_token = args[0]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']
    mock_update_learner_state = kwargs['update_learner_retirement_state']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)
    mock_get_retirement_state.return_value = get_fake_user_retirement(
        original_username=username,
        current_state_name='RETIRING_FORUMS'
    )

    result = _call_script(username)

    assert mock_get_access_token.call_count == 3
    mock_get_retirement_state.assert_called_once_with(username)
    mock_update_learner_state.assert_not_called()

    assert result.exit_code == ERR_USER_IN_WORKING_STATE
    assert 'in a working state' in result.output


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT
)
def test_user_in_bad_state(*args, **kwargs):
    username = 'test_username'
    bad_state = 'BOGUS_STATE'
    mock_get_access_token = args[0]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']
    mock_update_learner_state = kwargs['update_learner_retirement_state']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)
    mock_get_retirement_state.return_value = get_fake_user_retirement(
        original_username=username,
        current_state_name=bad_state
    )
    result = _call_script(username)

    assert mock_get_access_token.call_count == 3
    mock_get_retirement_state.assert_called_once_with(username)
    mock_update_learner_state.assert_not_called()

    assert result.exit_code == ERR_UNKNOWN_STATE
    assert bad_state in result.output


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT
)
def test_user_in_end_state(*args, **kwargs):
    username = 'test_username'

    mock_get_access_token = args[0]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']
    mock_update_learner_state = kwargs['update_learner_retirement_state']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)

    # pytest.parameterize doesn't play nicely with patch.multiple, this seemed more
    # readable than the alternatives.
    for end_state in END_STATES:
        mock_get_retirement_state.return_value = {
            'original_username': username,
            'current_state': {
                'state_name': end_state
            }
        }

        result = _call_script(username)

        assert mock_get_access_token.call_count == 3
        mock_get_retirement_state.assert_called_once_with(username)
        mock_update_learner_state.assert_not_called()

        assert result.exit_code == ERR_USER_AT_END_STATE
        assert end_state in result.output

        # Reset our call counts for the next test
        mock_get_access_token.reset_mock()
        mock_get_retirement_state.reset_mock()


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT,
    retirement_retire_forum=DEFAULT,
    retirement_retire_mailings=DEFAULT,
    retirement_unenroll=DEFAULT,
    retirement_lms_retire=DEFAULT
)
def test_skipping_states(*args, **kwargs):
    username = 'test_username'

    mock_get_access_token = args[0]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']
    mock_update_learner_state = kwargs['update_learner_retirement_state']
    mock_retire_forum = kwargs['retirement_retire_forum']
    mock_retire_mailings = kwargs['retirement_retire_mailings']
    mock_unenroll = kwargs['retirement_unenroll']
    mock_lms_retire = kwargs['retirement_lms_retire']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)
    mock_get_retirement_state.return_value = get_fake_user_retirement(
        original_username=username,
        current_state_name='EMAIL_LISTS_COMPLETE'
    )

    result = _call_script(username)

    # Called once per API we instantiate (LMS, ECommerce, Credentials)
    assert mock_get_access_token.call_count == 3
    mock_get_retirement_state.assert_called_once_with(username)
    assert mock_update_learner_state.call_count == 5

    # Skipped
    for mock_call in (
        mock_retire_forum,
        mock_retire_mailings
    ):
        mock_call.assert_not_called()

    # Called once per retirement
    for mock_call in (
        mock_unenroll,
        mock_lms_retire
    ):
        mock_call.assert_called_once_with(mock_get_retirement_state.return_value)

    assert result.exit_code == 0

    for required_output in (
        'RETIRING_FORUMS completed in previous run',
        'RETIRING_EMAIL_LISTS completed in previous run',
        'Starting state RETIRING_ENROLLMENTS',
        'State RETIRING_ENROLLMENTS completed',
        'Starting state RETIRING_LMS',
        'State RETIRING_LMS completed',
        'Retirement complete'
    ):
        assert required_output in result.output


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch('scripts.user_retirement.utils.edx_api.EcommerceApi.get_tracking_key')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT,
    retirement_retire_forum=DEFAULT,
    retirement_retire_mailings=DEFAULT,
    retirement_unenroll=DEFAULT,
    retirement_lms_retire=DEFAULT
)
def test_get_segment_id_success(*args, **kwargs):
    username = 'test_username'

    mock_get_tracking_key = args[0]
    mock_get_access_token = args[1]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']
    mock_retirement_retire_forum = kwargs['retirement_retire_forum']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)
    mock_get_tracking_key.return_value = {'id': 1, 'ecommerce_tracking_id': 'ecommerce-1'}

    # The learner starts off with these values, 'ecommerce_segment_id' is added during script
    # startup
    mock_get_retirement_state.return_value = get_fake_user_retirement(
        original_username=username,
    )

    _call_script(username, fetch_ecom_segment_id=True)
    mock_get_tracking_key.assert_called_once_with(mock_get_retirement_state.return_value)

    config_after_get_segment_id = mock_get_retirement_state.return_value
    config_after_get_segment_id['ecommerce_segment_id'] = 'ecommerce-1'

    mock_retirement_retire_forum.assert_called_once_with(config_after_get_segment_id)


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch('scripts.user_retirement.utils.edx_api.EcommerceApi.get_tracking_key')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT,
    retirement_retire_forum=DEFAULT,
    retirement_retire_mailings=DEFAULT,
    retirement_unenroll=DEFAULT,
    retirement_lms_retire=DEFAULT
)
def test_get_segment_id_not_found(*args, **kwargs):
    username = 'test_username'

    mock_get_tracking_key = args[0]
    mock_get_access_token = args[1]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)
    mock_get_tracking_key.side_effect = HttpDoesNotExistException('{} not found'.format(username))

    mock_get_retirement_state.return_value = get_fake_user_retirement(
        original_username=username,
    )

    result = _call_script(username, fetch_ecom_segment_id=True)
    mock_get_tracking_key.assert_called_once_with(mock_get_retirement_state.return_value)
    assert 'Setting Ecommerce Segment ID to None' in result.output

    # Reset our call counts for the next test
    mock_get_access_token.reset_mock()
    mock_get_retirement_state.reset_mock()


@patch('scripts.user_retirement.utils.edx_api.BaseApiClient.get_access_token')
@patch('scripts.user_retirement.utils.edx_api.EcommerceApi.get_tracking_key')
@patch.multiple(
    'scripts.user_retirement.utils.edx_api.LmsApi',
    get_learner_retirement_state=DEFAULT,
    update_learner_retirement_state=DEFAULT,
    retirement_retire_forum=DEFAULT,
    retirement_retire_mailings=DEFAULT,
    retirement_unenroll=DEFAULT,
    retirement_lms_retire=DEFAULT
)
def test_get_segment_id_error(*args, **kwargs):
    username = 'test_username'

    mock_get_tracking_key = args[0]
    mock_get_access_token = args[1]
    mock_get_retirement_state = kwargs['get_learner_retirement_state']
    mock_update_learner_state = kwargs['update_learner_retirement_state']

    mock_get_access_token.return_value = ('THIS_IS_A_JWT', None)

    test_exception_message = 'Test Exception!'
    mock_get_tracking_key.side_effect = Exception(test_exception_message)

    mock_get_retirement_state.return_value = get_fake_user_retirement(
        original_username=username,
    )

    mock_get_retirement_state.return_value = {
        'original_username': username,
        'current_state': {
            'state_name': 'PENDING'
        }
    }

    result = _call_script(username, fetch_ecom_segment_id=True)
    mock_get_tracking_key.assert_called_once_with(mock_get_retirement_state.return_value)
    mock_update_learner_state.assert_not_called()

    assert result.exit_code == ERR_SETUP_FAILED
    assert 'Unexpected error fetching Ecommerce tracking id!' in result.output
    assert test_exception_message in result.output
