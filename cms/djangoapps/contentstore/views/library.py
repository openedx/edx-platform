"""
Views related to content libraries.
A content library is a structure containing XBlocks which can be re-used in the
multiple courses.
"""
from __future__ import absolute_import

import json
import logging

from contentstore.views.item import create_xblock_info
from django.http import HttpResponseNotAllowed, Http404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.utils.translation import ugettext as _
from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator, LibraryUsageLocator
from xmodule.modulestore.django import modulestore

from .access import has_course_access
from .component import get_component_templates
from util.json_request import JsonResponse

__all__ = ['library_handler']

log = logging.getLogger(__name__)

LIBRARIES_ENABLED = settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES', False)


@login_required
@ensure_csrf_cookie
def library_handler(request, library_key_string=None):
    """
    RESTful interface to most content library related functionality.
    """
    if not LIBRARIES_ENABLED:
        raise Http404  # Should never happen because we test the feature in urls.py also

    response_format = 'html'
    if request.REQUEST.get('format', 'html') == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'text/html'):
        response_format = 'json'

    if library_key_string:
        library_key = CourseKey.from_string(library_key_string)
        if not isinstance(library_key, LibraryLocator):
            raise Http404  # This is not a library
        if not has_course_access(request.user, library_key):
            raise PermissionDenied()

        library = modulestore().get_library(library_key)
        if library is None:
            raise Http404

        if request.method == 'GET':
            return library_blocks_view(library, response_format)
        return HttpResponseNotAllowed(['GET'])

    elif request.method == 'GET':
        # List all accessible libraries:
        lib_info = [
            {
                "display_name": lib.display_name,
                "library_key": unicode(lib.location.library_key),
            }
            for lib in modulestore().get_libraries()
            if has_course_access(request.user, lib.location.library_key)
        ]
        return JsonResponse(lib_info)
    else:
        return HttpResponseNotAllowed(['GET'])


def library_blocks_view(library, response_format):
    """
    The main view of a course's content library.
    Shows all the XBlocks in the library, and allows adding/editing/deleting
    them.
    Can be called with response_format="json" to get a JSON-formatted list of
    the XBlocks in the library along with library metadata.
    """
    children = library.children
    if response_format == "json":
        # The JSON response for this request is short and sweet:
        prev_version = library.runtime.course_entry.structure['previous_version']
        return JsonResponse({
            "display_name": library.display_name,
            "library_id": unicode(library.location.course_key),  # library.course_id raises UndefinedContext - fix?
            "version": unicode(library.runtime.course_entry.course_key.version),
            "previous_version": unicode(prev_version) if prev_version else None,
            "blocks": [unicode(x) for x in children],
        })

    xblock_info = create_xblock_info(library, include_ancestor_info=False, graders=[])

    component_templates = get_component_templates(library)

    assert isinstance(library.location.library_key, LibraryLocator)
    assert isinstance(library.location, LibraryUsageLocator)

    return render_to_response('library.html', {
        'context_library': library,
        'action': 'view',
        'xblock': library,
        'xblock_locator': library.location,
        'unit': None,
        'component_templates': json.dumps(component_templates),
        'xblock_info': xblock_info,
    })
