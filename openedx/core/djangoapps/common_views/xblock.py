"""
Common views dedicated to rendering xblocks.
"""


import logging
import mimetypes

from django.http import Http404, HttpResponse
from xblock.core import XBlock, XBlock2

log = logging.getLogger(__name__)


def xblock_resource(request, block_type, uri, xblock_version=1):  # pylint: disable=unused-argument
    """
    Return a package resource for the specified XBlock.
    """
    try:
        # Figure out what the XBlock class is from the block type, and
        # then open whatever resource has been requested.
        if xblock_version == 2:
            xblock_class = XBlock2.load_class(block_type)
        else:
            xblock_class = XBlock.load_class(block_type)
        content = xblock_class.open_local_resource(uri)
    except OSError:
        log.info('Failed to load xblock resource', exc_info=True)
        raise Http404  # lint-amnesty, pylint: disable=raise-missing-from
    except Exception:
        log.error('Failed to load xblock resource', exc_info=True)
        raise Http404  # lint-amnesty, pylint: disable=raise-missing-from

    mimetype, _ = mimetypes.guess_type(uri)
    return HttpResponse(content, content_type=mimetype)


def xblock_resource_v2(request, block_type, uri):
    """
    Return a package resource for the specified v2 XBlock.
    """
    return xblock_resource(request, block_type, uri, xblock_version=2)
