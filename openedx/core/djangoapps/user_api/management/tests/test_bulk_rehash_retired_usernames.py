"""
Test the bulk_rehash_retired_usernames management command
"""
from mock import call, patch
import pytest

from django.conf import settings
from django.core.management import call_command
from user_util.user_util import get_retired_username

from lms.lib import comment_client
from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import RetirementTestCase, fake_retirement
from openedx.core.djangoapps.user_api.models import UserRetirementStatus
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def _setup_users():
    """
    Creates and returns test users in the different states of needing rehash:
    - Skipped: The retired username does not require updating, some of these are fake retired
    - Needing rehash: Has been fake-retired and name changed so it triggers a hash update
    """
    # When we loop through creating users, take additional action on these
    user_indexes_to_be_fake_retired = (2, 4, 6, 8, 10)
    user_indexes_to_be_rehashed = (4, 6)

    users_skipped = []
    users_needing_rehash = []
    retirements = {}

    # Create some test users with retirements
    for i in range(1, 11):
        user = UserFactory()
        retirement = UserRetirementStatus.create_retirement(user)
        retirements[user.id] = retirement

        if i in user_indexes_to_be_fake_retired:
            fake_retirement(user)

            if i in user_indexes_to_be_rehashed:
                # In order to need a rehash user.username the new hash must be
                # different, we force that here.
                retirement.retired_username = retirement.retired_username.upper()
                user.username = retirement.retired_username
                retirement.save()
                user.save()
                users_needing_rehash.append(user)
            else:
                users_skipped.append(user)
        else:
            users_skipped.append(user)
    return users_skipped, users_needing_rehash, retirements


@skip_unless_lms
@patch('lms.lib.comment_client.User.retire')
def test_successful_rehash(retire_user_forums, capsys):
    """
    Run the command with users of all different hash statuses, expect success
    """
    RetirementTestCase.setup_states()
    users_skipped, users_needing_rehash, retirements = _setup_users()

    call_command('bulk_rehash_retired_usernames')
    output = capsys.readouterr().out

    # Make sure forums was called the correct number of times
    assert retire_user_forums.call_count == 2

    for user in users_skipped:
        assert "User ID {} because the hash would not change.".format(user.id) in output

    expected_username_calls = []
    for user in users_needing_rehash:
        retirement = retirements[user.id]
        user.refresh_from_db()
        retirement.refresh_from_db()
        new_retired_username = get_retired_username(
            retirement.original_username,
            settings.RETIRED_USER_SALTS,
            settings.RETIRED_USERNAME_FMT
        )
        expected_username_calls.append(call(new_retired_username))

        assert "User ID {} to rehash their retired username".format(user.id) in output
        assert new_retired_username == user.username
        assert new_retired_username == retirement.retired_username

    retire_user_forums.assert_has_calls(expected_username_calls)


@skip_unless_lms
@patch('lms.lib.comment_client.User.retire')
def test_forums_failed(retire_user_forums, capsys):
    """
    Run the command with users of all different hash statuses, expect success
    """
    RetirementTestCase.setup_states()
    users_skipped, users_needing_rehash, retirements = _setup_users()
    retire_user_forums.side_effect = Exception('something bad happened with forums')

    call_command('bulk_rehash_retired_usernames')
    output = capsys.readouterr().out

    # Make sure forums was called the correct number of times
    assert retire_user_forums.call_count == 2

    for user in users_skipped:
        assert "User ID {} because the hash would not change.".format(user.id) in output

    expected_username_calls = []
    for user in users_needing_rehash:
        retirement = retirements[user.id]
        user.refresh_from_db()
        retirement.refresh_from_db()
        new_retired_username = get_retired_username(
            retirement.original_username,
            settings.RETIRED_USER_SALTS,
            settings.RETIRED_USERNAME_FMT
        )
        expected_username_calls.append(call(new_retired_username))

        assert "User ID {} to rehash their retired username".format(user.id) in output
        # Confirm that the usernames are *not* updated, due to the forums error
        assert new_retired_username != user.username
        assert new_retired_username != retirement.retired_username

    assert "FAILED! 2 retirements failed to rehash. Retirement IDs:" in output
    retire_user_forums.assert_has_calls(expected_username_calls)


@skip_unless_lms
@patch('lms.lib.comment_client.User.retire')
def test_forums_404(retire_user_forums, capsys):
    """
    Run the command with users of all different hash statuses, expect success
    """
    RetirementTestCase.setup_states()
    users_skipped, users_needing_rehash, retirements = _setup_users()
    retire_user_forums.side_effect = comment_client.utils.CommentClientRequestError('not found', status_codes=404)

    call_command('bulk_rehash_retired_usernames')
    output = capsys.readouterr().out

    # Make sure forums was called the correct number of times
    assert retire_user_forums.call_count == 2

    for user in users_skipped:
        assert "User ID {} because the hash would not change.".format(user.id) in output

    expected_username_calls = []
    for user in users_needing_rehash:
        retirement = retirements[user.id]
        user.refresh_from_db()
        retirement.refresh_from_db()
        new_retired_username = get_retired_username(
            retirement.original_username,
            settings.RETIRED_USER_SALTS,
            settings.RETIRED_USERNAME_FMT
        )
        expected_username_calls.append(call(new_retired_username))

        assert "User ID {} to rehash their retired username".format(user.id) in output
        # Confirm that the usernames *are* updated, since this is a non-blocking forums error
        assert new_retired_username == user.username
        assert new_retired_username == retirement.retired_username

    assert "Success!" in output
    retire_user_forums.assert_has_calls(expected_username_calls)
