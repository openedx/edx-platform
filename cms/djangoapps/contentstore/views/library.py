"""
Views related to content libraries.
A content library is a structure containing XBlocks which can be re-used in the
multiple courses.
"""
from __future__ import absolute_import

import json
import logging

from contentstore.views.item import create_xblock_info
from contentstore.utils import reverse_library_url, add_instructor
from django.http import HttpResponseNotAllowed, Http404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator, LibraryUsageLocator
from xmodule.modulestore.exceptions import DuplicateCourseError
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

from .component import get_component_templates, CONTAINER_TEMPATES
from student.auth import has_studio_write_access, has_studio_read_access
from student.roles import CourseCreatorRole
from student import auth
from util.json_request import expect_json, JsonResponse, JsonResponseBadRequest

__all__ = ['library_handler']

log = logging.getLogger(__name__)

LIBRARIES_ENABLED = settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES', False)


@login_required
@ensure_csrf_cookie
@require_http_methods(('GET', 'POST'))
def library_handler(request, library_key_string=None):
    """
    RESTful interface to most content library related functionality.
    """
    if not LIBRARIES_ENABLED:
        log.exception("Attempted to use the content library API when the libraries feature is disabled.")
        raise Http404  # Should never happen because we test the feature in urls.py also

    if library_key_string is not None and request.method == 'POST':
        return HttpResponseNotAllowed(("POST",))

    if request.method == 'POST':
        return _create_library(request)

    # request method is get, since only GET and POST are allowed by @require_http_methods(('GET', 'POST'))
    if library_key_string:
        return _display_library(library_key_string, request)

    return _list_libraries(request)


def _display_library(library_key_string, request):
    """
    Displays single library
    """
    library_key = CourseKey.from_string(library_key_string)
    if not isinstance(library_key, LibraryLocator):
        log.exception("Non-library key passed to content libraries API.")  # Should never happen due to url regex
        raise Http404  # This is not a library
    if not has_studio_read_access(request.user, library_key):
        log.exception(u"User %s tried to access library %s without permission", request.user.username, unicode(library_key))
        raise PermissionDenied()

    library = modulestore().get_library(library_key)
    if library is None:
        log.exception(u"Library %s not found", unicode(library_key))
        raise Http404

    response_format = 'html'
    if request.REQUEST.get('format', 'html') == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'text/html'):
        response_format = 'json'

    return library_blocks_view(library, request.user, response_format)


def _list_libraries(request):
    """
    List all accessible libraries
    """
    lib_info = [
        {
            "display_name": lib.display_name,
            "library_key": unicode(lib.location.library_key),
        }
        for lib in modulestore().get_libraries()
        if has_studio_read_access(request.user, lib.location.library_key)
    ]
    return JsonResponse(lib_info)


@expect_json
def _create_library(request):
    """
    Helper method for creating a new library.
    """
    if not auth.has_access(request.user, CourseCreatorRole()):
        log.exception(u"User %s tried to create a library without permission", request.user.username)
        raise PermissionDenied()
    display_name = None
    try:
        display_name = request.json['display_name']
        org = request.json['org']
        library = request.json.get('number', None)
        if library is None:
            library = request.json['library']
        store = modulestore()
        with store.default_store(ModuleStoreEnum.Type.split):
            new_lib = store.create_library(
                org=org,
                library=library,
                user_id=request.user.id,
                fields={"display_name": display_name},
            )
        # Give the user admin ("Instructor") role for this library:
        add_instructor(new_lib.location.library_key, request.user, request.user)
    except KeyError as error:
        log.exception("Unable to create library - missing required JSON key.")
        return JsonResponseBadRequest({
            "ErrMsg": _("Unable to create library - missing required field '{field}'".format(field=error.message))
        })
    except InvalidKeyError as error:
        log.exception("Unable to create library - invalid key.")
        return JsonResponseBadRequest({
            "ErrMsg": _("Unable to create library '{name}'.\n\n{err}").format(name=display_name, err=error.message)}
        )
    except DuplicateCourseError:
        log.exception("Unable to create library - one already exists with the same key.")
        return JsonResponseBadRequest({
            'ErrMsg': _(
                'There is already a library defined with the same '
                'organization and library code. Please '
                'change either organization or library code to be unique.'
            )
        })

    lib_key_str = unicode(new_lib.location.library_key)
    return JsonResponse({
        'url': reverse_library_url('library_handler', lib_key_str),
        'library_key': lib_key_str,
    })


def library_blocks_view(library, user, response_format):
    """
    The main view of a course's content library.
    Shows all the XBlocks in the library, and allows adding/editing/deleting
    them.
    Can be called with response_format="json" to get a JSON-formatted list of
    the XBlocks in the library along with library metadata.

    Assumes that read permissions have been checked before calling this.
    """
    assert isinstance(library.location.library_key, LibraryLocator)
    assert isinstance(library.location, LibraryUsageLocator)

    children = library.children
    if response_format == "json":
        # The JSON response for this request is short and sweet:
        prev_version = library.runtime.course_entry.structure['previous_version']
        return JsonResponse({
            "display_name": library.display_name,
            "library_id": unicode(library.location.library_key),
            "version": unicode(library.runtime.course_entry.course_key.version),
            "previous_version": unicode(prev_version) if prev_version else None,
            "blocks": [unicode(x) for x in children],
        })

    can_edit = has_studio_write_access(user, library.location.library_key)

    xblock_info = create_xblock_info(library, include_ancestor_info=False, graders=[])
    component_templates = get_component_templates(library, library=True) if can_edit else []

    return render_to_response('library.html', {
        'can_edit': can_edit,
        'context_library': library,
        'component_templates': json.dumps(component_templates),
        'xblock_info': xblock_info,
        'templates': CONTAINER_TEMPATES,
        'lib_users_url': reverse_library_url('manage_library_users', unicode(library.location.library_key)),
    })
