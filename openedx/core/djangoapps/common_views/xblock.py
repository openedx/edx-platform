"""
Common views dedicated to rendering xblocks.
"""
from __future__ import absolute_import

import logging
import mimetypes
import pkg_resources

from xblock.core import XBlock

from django.conf import settings
from django.http import Http404, HttpResponse


log = logging.getLogger(__name__)


def xblock_resource(request, block_type, uri):  # pylint: disable=unused-argument
    """
    Return a package resource for the specified XBlock.
    """
    try:
        # Figure out what the XBlock class is from the block type, and
        # then open whatever resource has been requested.
        xblock_class = XBlock.load_class(block_type, select=settings.XBLOCK_SELECT_FUNCTION)
        content = xblock_class.open_local_resource(uri)
    except IOError:
        log.info('Failed to load xblock resource', exc_info=True)
        raise Http404
    except Exception:
        log.error('Failed to load xblock resource', exc_info=True)
        raise Http404

    mimetype, _ = mimetypes.guess_type(uri)
    return HttpResponse(content, content_type=mimetype)
