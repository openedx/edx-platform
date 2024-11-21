"""
Tasks for offline mode feature.
"""
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from django.http.response import Http404
from opaque_keys.edx.keys import CourseKey, UsageKey

from xmodule.modulestore.django import modulestore

from .assets_management import is_modified
from .constants import MAX_RETRY_ATTEMPTS, OFFLINE_SUPPORTED_XBLOCKS, RETRY_BACKOFF_INITIAL_TIMEOUT
from .renderer import XBlockRenderer
from .storage_management import OfflineContentGenerator


@shared_task
@set_code_owner_attribute
def generate_offline_content_for_course(course_id):
    """
    Generates offline content for all supported XBlocks in the course.

    Blocks that are closed to responses won't be processed.
    """
    course_key = CourseKey.from_string(course_id)
    for offline_supported_block_type in OFFLINE_SUPPORTED_XBLOCKS:
        for xblock in modulestore().get_items(course_key, qualifiers={'category': offline_supported_block_type}):
            is_not_closed = not hasattr(xblock, 'closed') or not xblock.closed()
            if is_not_closed and is_modified(xblock):
                generate_offline_content_for_block.apply_async([str(xblock.location)])


@shared_task(
    autoretry_for=(Http404,),
    retry_backoff=RETRY_BACKOFF_INITIAL_TIMEOUT,
    retry_kwargs={'max_retries': MAX_RETRY_ATTEMPTS}
)@set_code_owner_attribute
def generate_offline_content_for_block(block_id):
    """
    Generates offline content for the specified block.
    """
    block_usage_key = UsageKey.from_string(block_id)
    xblock = modulestore().get_item(block_usage_key)
    OfflineContentGenerator(xblock).generate_offline_content()
