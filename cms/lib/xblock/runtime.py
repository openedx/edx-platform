"""
XBlock runtime implementations for edX Studio
"""

from __future__ import absolute_import

import six
from django.urls import reverse


def handler_url(block, handler_name, suffix='', query='', thirdparty=False):
    """
    Handler URL function for Studio
    """

    if thirdparty:
        raise NotImplementedError("edX Studio doesn't support third-party xblock handler urls")

    url = reverse('component_handler', kwargs={
        'usage_key_string': six.text_type(block.scope_ids.usage_id),
        'handler': handler_name,
        'suffix': suffix,
    }).rstrip('/')

    if query:
        url += '?' + query

    return url
