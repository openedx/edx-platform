"""
Utility functions for offline mode.
"""

import logging
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage

from xmodule.modulestore.django import modulestore

from .constants import OFFLINE_SUPPORTED_XBLOCKS

User = get_user_model()
log = logging.getLogger(__name__)


def get_offline_service_user():
    """
    Get the service user to render XBlock.
    """
    try:
        return User.objects.get(username=settings.OFFLINE_SERVICE_WORKER_USERNAME)
    except User.DoesNotExist as e:
        log.error(
            f"Service user with username {settings.OFFLINE_SERVICE_WORKER_USERNAME} to render XBlock does not exist."
        )
        raise e


def clear_deleted_content(course_key):
    """
    Delete the offline content archive for the blocks that are deleted from the course.
    """
    base_offline_course_path = settings.OFFLINE_CONTENT_PATH_TEMPLATE.format(course_id=str(course_key))
    if default_storage.exists(base_offline_course_path):
        _, file_names = default_storage.listdir(base_offline_course_path)
    else:
        return

    all_course_offline_archive_names = {
        f"{xblock.location.block_id}.zip"
        for block_type in OFFLINE_SUPPORTED_XBLOCKS
        for xblock in modulestore().get_items(course_key, qualifiers={"category": block_type})
    }

    files_to_delete = set(file_names) - all_course_offline_archive_names

    for file_name in files_to_delete:
        file_path = os.path.join(base_offline_course_path, file_name)
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            log.info(f"Successfully deleted the file: {file_path}")
