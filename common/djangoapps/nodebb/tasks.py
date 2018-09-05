"""
Tasks to synchronize users with NodeBB
"""
from celery.utils.log import get_task_logger

from django.conf import settings
from requests.exceptions import ConnectionError
from celery.task import task

from common.lib.nodebb_client.client import NodeBBClient

LOGGER = get_task_logger(__name__)

RETRY_DELAY = settings.NODEBB_RETRY_DELAY  # seconds

# TODO: REMOVE THIS BEFORE PUSHING
# settings.CELERY_ALWAYS_EAGER = False
# RETRY_DELAY = 20


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_create_user_on_nodebb(username, user_data):
    """
    Celery task to create user on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.create(username=username, user_data=user_data)
        if status_code == 200:
            LOGGER.debug('Success: User creation task for user: {}'.format(username))
        else:
            LOGGER.error('Failure: User creation task for user: {}, status_code: {}, response: {}'
                         .format(username, status_code, response))
    except ConnectionError as exc:
        LOGGER.debug('Retrying: User creation task for user: {}'.format(username))
        task_create_user_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_update_user_profile_on_nodebb(username, profile_data):
    """
    Celery task to update user profile info on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.update_profile(username=username, profile_data=profile_data)
        if status_code == 200:
            LOGGER.debug('Success: Update user profile task for user: {}'.format(username))
        else:
            LOGGER.error('Failure: Update user profile task for user: {}, status_code: {}, response: {}'
                         .format(username, status_code, response))
    except ConnectionError as exc:
        LOGGER.debug('Retrying: Update user profile task for user: {}'.format(username))
        task_update_user_profile_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_delete_user_on_nodebb(username):
    """
    Celery task to delete user on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.delete_user(username)
        if status_code == 200:
            LOGGER.debug('Success: Delete user task for user: {}'.format(username))
        else:
            LOGGER.error('Failure: Delete user task for user: {}, status_code: {}, response: {}'
                         .format(username, status_code, response))
    except ConnectionError as exc:
        LOGGER.debug('Retrying: Delete user task for user: {}'.format(username))
        task_delete_user_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_activate_user_on_nodebb(username, active):
    """
    Celery task to activate user on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.activate(username=username, active=active)
        if status_code == 200:
            LOGGER.debug('Success: Activate user task for user: {}'.format(username))
        else:
            LOGGER.error('Failure: Activate user task for user: {}, status_code: {}, response: {}'
                         .format(username, status_code, response))
    except ConnectionError as exc:
        LOGGER.debug('Retrying: Activate user task for user: {}'.format(username))
        task_activate_user_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_join_group_on_nodebb(group_name, username):
    """
    Celery task to join user to a community on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.join(group_name=group_name, username=username)
        if status_code == 200:
            LOGGER.debug('Success: Join user task for user: {} and community/group: {}'.format(username, group_name))
        else:
            LOGGER.error('Failure: Join user task for user: {}, group_name: {}, status_code: {}, response: {}'
                         .format(username, group_name, status_code, response))
    except ConnectionError as exc:
        LOGGER.debug('Retrying: Join user task for user: {} and community/group: {}'.format(username, group_name))
        task_join_group_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_update_onboarding_surveys_status(username):
    """
    Celery task to update survey status for username on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.update_onboarding_surveys_status(username=username)
        if status_code == 200:
            LOGGER.debug('Success: Update Onboarding Survey task for user: {}'.format(username))
        else:
            LOGGER.error('Failure: Update Onboarding Survey task for user: {}, status_code: {}, response: {}'
                         .format(username, status_code, response))
    except ConnectionError as exc:
        LOGGER.debug('Retrying: Update Onboarding Survey task for user: {}'.format(username))
        task_update_onboarding_surveys_status.retry(exc=exc)
