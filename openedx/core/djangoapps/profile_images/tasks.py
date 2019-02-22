"""
This file contains celery tasks for profile_images
"""
from __future__ import absolute_import

from celery.task import task
from celery.utils.log import get_task_logger

from ..user_api.accounts.image_helpers import get_profile_image_names
from .images import remove_profile_images


LOGGER = get_task_logger(__name__)


@task
def delete_profile_images(usernames):
    """
    Delete profile images from storage belonging to usernames.

    Arguments:
        usernames: list of usernames
    """
    for username in usernames:
        profile_image_names = get_profile_image_names(username)
        LOGGER.info('Deleting profile images for %s...', username)
        try:
            remove_profile_images(profile_image_names)
        except Exception as e:
            LOGGER.exception('Failed to delete profile images for %s. Error: %s', username, e)
