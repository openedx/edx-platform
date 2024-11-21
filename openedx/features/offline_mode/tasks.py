"""
Tasks for offline mode feature.
"""
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey, UsageKey

from xmodule.modulestore.django import modulestore

from .constants import OFFLINE_SUPPORTED_XBLOCKS
from .renderer import XBlockRenderer
from .utils import generate_offline_content


@shared_task
@set_code_owner_attribute
def generate_offline_content_for_course(course_id):
    """
    Generates offline content for all supported XBlocks in the course.
    """
    course_key = CourseKey.from_string(course_id)
    for offline_supported_block_type in OFFLINE_SUPPORTED_XBLOCKS:
        for xblock in modulestore().get_items(course_key, qualifiers={'category': offline_supported_block_type}):
            html_data = XBlockRenderer(str(xblock.location)).render_xblock_from_lms()
            generate_offline_content_for_block.apply_async([str(xblock.location), html_data])


@shared_task
@set_code_owner_attribute
def generate_offline_content_for_block(block_id, html_data):
    """
    Generates offline content for the specified block.
    """
    block_usage_key = UsageKey.from_string(block_id)
    xblock = modulestore().get_item(block_usage_key)
    generate_offline_content(xblock, html_data)
