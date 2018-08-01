"""
Tasks to synchronize users with NodeBB
"""
from logging import getLogger

from requests.exceptions import ConnectionError
from celery.task import task

from common.lib.nodebb_client.client import NodeBBClient

log = getLogger(__name__)

RETRY_DELAY = 20 # seconds

@task(bind=True, default_retry_delay=RETRY_DELAY, max_retries=None)
def task_create_user_on_nodebb(self, username, **kwargs):
    """
    Celery task to create user on NodeBB
    """
    try:
        NodeBBClient().users.create(username=username, kwargs=kwargs)
        log.info('Success: User creation task for user: {}'.format(username))
    except ConnectionError:
        log.info('Retrying: User creation task for user: {}'.format(username))
        self.retry()

@task(bind=True, default_retry_delay=RETRY_DELAY, max_retries=None)
def task_update_user_profile_on_nodebb(self, username, **kwargs):
    """
    Celery task to update user profile info on NodeBB
    """
    try:
        NodeBBClient().users.update_profile(username=username, kwargs=kwargs)
        log.info('Success: Update user profile task for user: {}'.format(username))
    except ConnectionError:
        log.info('Retrying: Update user profile task for user: {}'.format(username))
        self.retry()

@task(bind=True, default_retry_delay=RETRY_DELAY, max_retries=None)
def task_delete_user_on_nodebb(self, username, **kwargs):
    """
    Celery task to delete user on NodeBB
    """
    try:
        NodeBBClient().users.delete_user(username, kwargs=kwargs)
        log.info('Success: Delete user task for user: {}'.format(username))
    except ConnectionError:
        log.info('Retrying: Delete user task for user: {}'.format(username))
        self.retry()

@task(bind=True, default_retry_delay=RETRY_DELAY, max_retries=None)
def task_activate_user_on_nodebb(self, username, active, **kwargs):
    """
    Celery task to activate user on NodeBB
    """
    try:
        NodeBBClient().users.activate(username=username, active=)