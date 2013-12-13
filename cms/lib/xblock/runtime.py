"""
XBlock runtime implementations for edX Studio
"""

from django.core.urlresolvers import reverse

from lms.lib.xblock.runtime import quote_slashes


def handler_url(block, handler_name, suffix='', query='', thirdparty=False):
    """
    Handler URL function for Studio
    """

    if thirdparty:
        raise NotImplementedError("edX Studio doesn't support third-party xblock handler urls")

    url = reverse('component_handler', kwargs={
        'usage_id': quote_slashes(str(block.scope_ids.usage_id)),
        'handler': handler_name,
        'suffix': suffix,
    }).rstrip('/')

    if query:
        url += '?' + query

    return url

