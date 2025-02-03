"""
Tasks for offline mode feature.
"""
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from django.http.response import Http404
from opaque_keys.edx.keys import CourseKey, UsageKey

from lms.djangoapps.course_blocks.api import get_course_blocks
from xmodule.modulestore.django import modulestore

from .assets_management import is_modified
from .constants import MAX_RETRY_ATTEMPTS, OFFLINE_SUPPORTED_XBLOCKS, RETRY_BACKOFF_INITIAL_TIMEOUT
from .storage_management import OfflineContentGenerator
from .utils import get_offline_service_user


@shared_task
@set_code_owner_attribute
def generate_offline_content_for_course(course_id):
    """
    Generates offline content for all supported XBlocks in the course.

    Blocks that are closed to responses won't be processed.
    """
    course_key = CourseKey.from_string(course_id)
    root_block_usage_key = modulestore().make_course_usage_key(course_key)
    user = get_offline_service_user()
    blocks = get_course_blocks(user, root_block_usage_key)
    for block_usage_key in blocks:
        if block_usage_key.block_type in OFFLINE_SUPPORTED_XBLOCKS:
            generate_offline_content_for_block.apply_async([str(block_usage_key)])


@shared_task(
    autoretry_for=(Http404,),
    retry_backoff=RETRY_BACKOFF_INITIAL_TIMEOUT,
    retry_kwargs={'max_retries': MAX_RETRY_ATTEMPTS}
)
@set_code_owner_attribute
def generate_offline_content_for_block(block_id):
    """
    Generates offline content for the specified block.
    """
    block_usage_key = UsageKey.from_string(block_id)
    xblock = modulestore().get_item(block_usage_key)
    is_not_closed = not hasattr(xblock, 'closed') or not xblock.closed()
    if is_not_closed and is_modified(xblock):
        OfflineContentGenerator(xblock).generate_offline_content()
