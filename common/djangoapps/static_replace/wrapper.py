"""
Wrapper function to replace static/course/jump-to-id URLs in XBlock to absolute URLs
"""

from openedx.core.lib.xblock_utils import wrap_fragment


def replace_urls_wrapper(block, view, frag, context, replace_url_service, static_replace_only=False):  # pylint: disable=unused-argument
    """
    Replace any static/course/jump-to-id URLs in XBlock to absolute URLs
    """
    return wrap_fragment(frag, replace_url_service.replace_urls(frag.content, static_replace_only))
