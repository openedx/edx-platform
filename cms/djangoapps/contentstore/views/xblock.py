"""
Views dedicated to rendering xblocks.
"""
from __future__ import absolute_import

import logging
import mimetypes

from xblock.core import XBlock

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext as _


log = logging.getLogger(__name__)


def xblock_resource(request, block_type, uri):  # pylint: disable=unused-argument
    """
    Return a package resource for the specified XBlock.
    """
    try:
        xblock_class = XBlock.load_class(block_type, settings.XBLOCK_SELECT_FUNCTION)
        content = xblock_class.open_local_resource(uri)
    except IOError:
        log.info('Failed to load xblock resource', exc_info=True)
        raise Http404
    except Exception:  # pylint: disable-msg=broad-except
        log.error('Failed to load xblock resource', exc_info=True)
        raise Http404

    mimetype, _ = mimetypes.guess_type(uri)
    return HttpResponse(content, mimetype=mimetype)


def get_course_xblock_type_info(course_module):
    """
    Returns information about xblock types used within the course.
    """
    json = {}
    xblock_types_json = []
    xblocks_dict = {}
    _populate_course_xblocks_dict(xblocks_dict, course_module)
    for name, xblock_class in XBlock.load_classes():
        display_name = get_xblock_type_display_name(name)
        xblocks = xblocks_dict.get(name, [])
        studio_url = reverse('contentstore.views.dashboard_handler', kwargs={
            'course_key_string': course_module.id,
            'xblock_type_name': name,
        })
        xblock_type_json = {
            'id': name,
            'display_name': display_name,
            'locators': list(unicode(xblock.scope_ids.usage_id) for xblock in xblocks),
            'studio_url': studio_url,
        }
        xblock_types_json.append(xblock_type_json)
    xblock_types_json.sort(key=lambda item: item['display_name'])
    json['xblock_types'] = xblock_types_json
    return json


def _populate_course_xblocks_dict(xblocks_dict, xblock):
    """
    Populates a dict with information about the xblock and all of its children.
    """
    category = xblock.category
    if category not in xblocks_dict:
        xblocks_dict[category] = []
    xblocks_dict[category].append(xblock)
    for child in xblock.get_children():
        _populate_course_xblocks_dict(xblocks_dict, child)


def get_xblock_type_display_name(xblock_type_name):
    """
    Returns the display name for the specified xblock type name.
    """
    component_class = XBlock.load_class(xblock_type_name, select=settings.XBLOCK_SELECT_FUNCTION)
    if hasattr(component_class, 'display_name'):
        display_name = component_class.display_name.default
        if display_name and not display_name == 'Empty':
            return _(display_name)
    return xblock_type_name
