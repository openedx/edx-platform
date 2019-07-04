"""
Tasks to synchronize users with NodeBB
"""
from celery.utils.log import get_task_logger

from django.conf import settings
from django.contrib.auth.models import User
from celery.task import task

from common.lib.nodebb_client.client import NodeBBClient

LOGGER = get_task_logger(__name__)

RETRY_DELAY = settings.NODEBB_RETRY_DELAY  # seconds

# TODO: REMOVE THIS BEFORE PUSHING
# settings.CELERY_ALWAYS_EAGER = False
# RETRY_DELAY = 20


def handle_response(caller, task_name, status_code, response, username):
    """
    Logs the response of the specific NodeBB API call
    """
    if status_code >= 500:
        print('Retrying: {} task for user: {}'.format(task_name, username))
        caller.retry()
    elif status_code >= 400:
        print('Failure: {} task for user: {}, status_code: {}, response: {}'
              .format(task_name, username, status_code, response))
    elif status_code >= 200 and status_code < 300:
        print('Success: {} task for user: {}'.format(task_name, username))


@task(default_retry_delay=RETRY_DELAY, max_retries=None, routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_create_user_on_nodebb(username, user_data):
    """
    Celery task to create user on NodeBB
    """
    status_code, response = NodeBBClient().users.create(username=username, user_data=user_data)
    handle_response(task_create_user_on_nodebb, 'User creation', status_code, response, username)
    if status_code == 200:
        try:
            user = User.objects.filter(username=username)[0]
        except IndexError:
            # if user does not exist then return
            return
        if user.is_active:
            task_activate_user_on_nodebb.delay(username=username, active=True)
        # if user has completed all registration forms then update the status on NodeBB
        if not bool(user.extended_profile.unattended_surveys(_type='list')):
            task_update_onboarding_surveys_status.delay(username)


@task(default_retry_delay=RETRY_DELAY, max_retries=None, routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_update_user_profile_on_nodebb(username, profile_data):
    """
    Celery task to update user profile info on NodeBB
    """
    status_code, response = NodeBBClient().users.update_profile(username=username, profile_data=profile_data)
    handle_response(task_update_user_profile_on_nodebb, 'Update user profile', status_code, response, username)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_delete_user_on_nodebb(username):
    """
    Celery task to delete user on NodeBB
    """
    status_code, response = NodeBBClient().users.delete_user(username)
    handle_response(task_delete_user_on_nodebb, 'Delete user', status_code, response, username)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_activate_user_on_nodebb(username, active):
    """
    Celery task to activate user on NodeBB
    """
    status_code, response = NodeBBClient().users.activate(username=username, active=active)
    handle_response(task_activate_user_on_nodebb, 'Activate user', status_code, response, username)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_join_group_on_nodebb(category_id, username):
    """
    Celery task to join user to a community on NodeBB
    """
    status_code, response = NodeBBClient().users.join(category_id=category_id, username=username)
    handle_response(task_join_group_on_nodebb, 'Join user in category with id {}'.format(category_id), status_code, response, username)


@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_un_join_group_on_nodebb(category_id, username):
    """
    Celery task to join user to a community on NodeBB
    """
    status_code, response = NodeBBClient().users.un_join(category_id=category_id, username=username)
    handle_response(task_un_join_group_on_nodebb, 'Removed user from category with id {}'.format(category_id), status_code, response, username)




@task(default_retry_delay=RETRY_DELAY, max_retries=None)
def task_update_onboarding_surveys_status(username):
    """
    Celery task to update survey status for username on NodeBB
    """
    status_code, response = NodeBBClient().users.update_onboarding_surveys_status(username=username)
    handle_response(task_update_onboarding_surveys_status, 'Update Onboarding Survery', status_code, response, username)
