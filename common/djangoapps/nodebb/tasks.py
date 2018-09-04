"""
Tasks to synchronize users with NodeBB
"""
from logging import getLogger

from django.conf import settings
from requests.exceptions import ConnectionError
from celery.task import task

from common.lib.nodebb_client.client import NodeBBClient

log = getLogger(__name__)

RETRY_DELAY = settings.NODEBB_RETRY_DELAY  # seconds

settings.CELERY_ALWAYS_EAGER = False


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_create_user_on_nodebb(username, user_data):
    """
    Celery task to create user on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.create(username=username, user_data=user_data)
        if status_code != 200:
            print 'status_code: {}, response: {}'.format(status_code, response)
        log.info('Success: User creation task for user: {}'.format(username))
    except ConnectionError as exc:
        log.info('Retrying: User creation task for user: {}'.format(username))
        print 'Retrying: User creation task for user: {}'.format(username)
        task_create_user_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_update_user_profile_on_nodebb(username, profile_data):
    """
    Celery task to update user profile info on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.update_profile(username=username, profile_data=profile_data)
        if status_code != 200:
            print 'status_code: {}, response: {}'.format(status_code, response)
        log.info('Success: Update user profile task for user: {}'.format(username))
    except ConnectionError as exc:
        log.info('Retrying: Update user profile task for user: {}'.format(username))
        print 'Retrying: Update user profile task for user: {}'.format(username)
        task_update_user_profile_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_delete_user_on_nodebb(username):
    """
    Celery task to delete user on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.delete_user(username)
        if status_code != 200:
            print 'status_code: {}, response: {}'.format(status_code, response)
        log.info('Success: Delete user task for user: {}'.format(username))
        print 'Success: Delete user task for user: {}'.format(username)
    except ConnectionError as exc:
        log.info('Retrying: Delete user task for user: {}'.format(username))
        print 'Retrying: Delete user task for user: {}'.format(username)
        task_delete_user_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_activate_user_on_nodebb(username, active):
    """
    Celery task to activate user on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.activate(username=username, active=active)
        if status_code != 200:
            print 'status_code: {}, response: {}'.format(status_code, response)
        log.info('Success: Activate user task for user: {}'.format(username))
    except ConnectionError as exc:
        log.info('Retrying: Activate user task for user: {}'.format(username))
        print 'Retrying: Activate user task for user: {}'.format(username)
        task_activate_user_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_join_group_on_nodebb(group_name, username):
    """
    Celery task to join user to a community on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.join(group_name=group_name, username=username)
        if status_code != 200:
            print 'status_code: {}, response: {}'.format(status_code, response)
        log.info('Success: Join user task for user: {} and community/group: {}'.format(username, group_name))
    except ConnectionError as exc:
        log.info('Retrying: Join user task for user: {} and community/group: {}'.format(username, group_name))
        print 'Retrying: Join user task for user: {} and community/group: {}'.format(username, group_name)
        task_join_group_on_nodebb.retry(exc=exc)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_update_onboarding_surveys_status(username):
    """
    Celery task to update survey status for username on NodeBB
    """
    try:
        status_code, response = NodeBBClient().users.update_onboarding_surveys_status(username=username)
        if status_code != 200:
            print 'status_code: {}, response: {}'.format(status_code, response)
        log.info('Success: Update Onboarding Survey task for user: {}'.format(username))
        print 'Success: Update Onboarding Survey task for user: {}'.format(username)
    except ConnectionError as exc:
        log.info('Retrying: Update Onboarding Survey task for user: {}'.format(username))
        print 'Retrying: Update Onboarding Survey task for user: {}'.format(username)
        task_update_onboarding_surveys_status.retry(exc=exc)
