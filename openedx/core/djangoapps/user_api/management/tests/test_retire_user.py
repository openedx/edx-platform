"""
Test the retire_user management command
"""


import pytest
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.management import CommandError, call_command

from ...models import UserRetirementStatus
from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import (  # lint-amnesty, pylint: disable=unused-import, wrong-import-order
    setup_retirement_states
)
from openedx.core.djangolib.testing.utils import skip_unless_lms  # lint-amnesty, pylint: disable=wrong-import-order
from common.djangoapps.student.tests.factories import UserFactory  # lint-amnesty, pylint: disable=wrong-import-order
import csv
import os

pytestmark = pytest.mark.django_db
user_file = 'userfile.csv'


def create_user_file(other_email=False):
    """
    Function to create a comma spearated file with username and password

    Args:
        other_email (bool, optional): test user with email mimatch. Defaults to False.
    """
    user1 = UserFactory.create(username='user1', email="user1@example.com")
    user2 = UserFactory.create(username='user2', email="user2@example.com")
    user3 = UserFactory.create(username='user3', email="user3@example.com")
    if other_email:
        user3.email = "other@edx.org"
    user_list = [{'username': user1.username, 'email': user1.email},
                 {'username': user2.username, 'email': user2.email},
                 {'username': user3.username, 'email': user3.email}]
    with open(user_file, 'w', newline='') as file:
        write = csv.writer(file)
        for user in user_list:
            write.writerow(user.values())


def remove_user_file():
    """
    Function to remove user file
    """
    if os.path.exists(user_file):
        os.remove(user_file)


@skip_unless_lms
def test_successful_retire(setup_retirement_states):  # lint-amnesty, pylint: disable=redefined-outer-name, unused-argument
    user = UserFactory.create(username='user1', email="user1@example.com")
    username = user.username
    user_email = user.email
    create_user_file()
    call_command('retire_user', user_file=user_file)
    user = User.objects.get(username=username)
    retired_user_status = UserRetirementStatus.objects.all()[0]
    assert retired_user_status.original_username == username
    assert retired_user_status.original_email == user_email
    # Make sure that we have changed the email address linked to the original user
    assert user.email != user_email
    remove_user_file()


@skip_unless_lms
def test_retire_user_with_usename_email_mismatch(setup_retirement_states):  # lint-amnesty, pylint: disable=redefined-outer-name, unused-argument
    create_user_file(True)
    with pytest.raises(CommandError, match=r'Could not find a user with specified username and email '):
        call_command('retire_user', user_file=user_file)
    remove_user_file()
