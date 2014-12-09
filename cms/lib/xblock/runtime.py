"""
XBlock runtime implementations for edX Studio
"""

from django.core.urlresolvers import reverse


def handler_url(block, handler_name, suffix='', query='', thirdparty=False):
    """
    Handler URL function for Studio
    """

    if thirdparty:
        raise NotImplementedError("edX Studio doesn't support third-party xblock handler urls")

    url = reverse('component_handler', kwargs={
        'usage_key_string': unicode(block.scope_ids.usage_id).encode('utf-8'),
        'handler': handler_name,
        'suffix': suffix,
    }).rstrip('/')

    if query:
        url += '?' + query

    return url


def local_resource_url(block, uri):
    """
    local_resource_url for Studio
    """
    return reverse('xblock_resource_url', kwargs={
        'block_type': block.scope_ids.block_type,
        'uri': uri,
    })


def applicable_aside_types(block):  # pylint: disable=unused-argument
    """
    Get the application-relative list of aside types for this type of block.
    """
    # TODO: Implement this method to make XBlockAsides for editing views in Studio
    return []
