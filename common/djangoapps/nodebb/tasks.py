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
        print 'Success: User creation task for user: {}'.format(username)
    except ConnectionError:
        print 'Retrying: User creation task for user: {}'.format(username)
        self.retry()

@task(bind=True, default_retry_delay=RETRY_DELAY, max_retries=None)
def task_update_user_profile_on_nodebb(self, username, **kwargs):
    """
    Celery task to update user profile info on NodeBB
    """
    try:
        NodeBBClient().users.update_profile(username=username, kwargs=kwargs)
        print 'Success: Update user profile task for user: {}'.format(username)
    except ConnectionError:
        print 'Retrying: Update user profile task for user: {}'.format(username)
        self.retry()

@task(bind=True, default_retry_delay=RETRY_DELAY, max_retries=None)
def task_delete_user_on_nodebb(self, username, **kwargs):
    """
    Celery task to delete user on NodeBB
    """
    try:
        NodeBBClient().users.delete_user(username, kwargs=kwargs)
        print 'Success: Delete user task for user: {}'.format(username)
    except ConnectionError:
        print 'Retrying: Delete user task for user: {}'.format(username)
        self.retry()

@task(bind=True, default_retry_delay=RETRY_DELAY, max_retries=None)
def task_activate_user_on_nodebb(self, username, active, **kwargs):
    """
    Celery task to activate user on NodeBB
    """
    try:
        NodeBBClient().users.activate(username=username, active=active)
        print 'Success: Activate user task for user: {}'.format(username)
    except ConnectionError:
        print 'Retrying: Activate user task for user: {}'.format(username)
        self.retry()

@task(bind=True, default_retry_delay=RETRY_DELAY, max_retries=None)
def task_join_group_on_nodebb(self, group_name, username):
    """
    Celery task to join user to a community on NodeBB
    """
    try:
        NodeBBClient().users.join(group_name=group_name, username=username)
        print 'Success: Join user task for user: {} and community/group: {}'.format(username, group_name)
    except ConnectionError:
        print 'Retrying: Join user task for user: {} and community/group: {}'.format(username, group_name)
        self.retry()

@task(bind=True, default_retry_delay=RETRY_DELAY, max_retries=None)
def task_update_onboarding_surveys_status(self, username):
    """
    Celery task to update survey status for username on NodeBB
    """
    try:
        NodeBBClient().users.update_onboarding_surveys_status(username=username)
        print 'Success: Update Onboarding Survey task for user: {}'.format(username)
    except ConnectionError:
        print 'Retrying: Update Onboarding Survey task for user: {}'.format(username)
        self.retry()
