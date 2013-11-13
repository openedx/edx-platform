import logging
from functools import partial

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response, render_to_string

from xmodule_modifiers import replace_static_urls, wrap_xblock
from xmodule.error_module import ErrorDescriptor
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.modulestore.django import modulestore
from xmodule.x_module import ModuleSystem
from xblock.runtime import DbModel
from xblock.django.request import webob_to_django_response, django_to_webob_request
from xblock.exceptions import NoSuchHandlerError

from lms.lib.xblock.field_data import LmsFieldData
from lms.lib.xblock.runtime import quote_slashes, unquote_slashes

from util.sandboxing import can_execute_unsafe_code

import static_replace
from .session_kv_store import SessionKeyValueStore
from .helpers import render_from_lms
from .access import has_access
from ..utils import get_course_for_item

__all__ = ['preview_handler', 'preview_component']

log = logging.getLogger(__name__)


def handler_prefix(block, handler='', suffix=''):
    """
    Return a url prefix for XBlock handler_url. The full handler_url
    should be '{prefix}/{handler}/{suffix}?{query}'.

    Trailing `/`s are removed from the returned url.
    """
    return reverse('preview_handler', kwargs={
        'usage_id': quote_slashes(str(block.scope_ids.usage_id)),
        'handler': handler,
        'suffix': suffix,
    }).rstrip('/?')


@login_required
def preview_handler(request, usage_id, handler, suffix=''):
    """
    Dispatch an AJAX action to an xblock

    usage_id: The usage-id of the block to dispatch to, passed through `quote_slashes`
    handler: The handler to execute
    suffix: The remaineder of the url to be passed to the handler
    """

    location = unquote_slashes(usage_id)

    descriptor = modulestore().get_item(location)
    instance = load_preview_module(request, descriptor)
    # Let the module handle the AJAX
    req = django_to_webob_request(request)
    try:
        resp = instance.handle(handler, req, suffix)

    except NoSuchHandlerError:
        log.exception("XBlock %s attempted to access missing handler %r", instance, handler)
        raise Http404

    except NotFoundError:
        log.exception("Module indicating to user that request doesn't exist")
        raise Http404

    except ProcessingError:
        log.warning("Module raised an error while processing AJAX request",
                    exc_info=True)
        return HttpResponseBadRequest()

    except Exception:
        log.exception("error processing ajax call")
        raise

    return webob_to_django_response(resp)


@login_required
def preview_component(request, location):
    "Return the HTML preview of a component"
    # TODO (vshnayder): change name from id to location in coffee+html as well.
    if not has_access(request.user, location):
        return HttpResponseForbidden()

    component = modulestore().get_item(location)
    # Wrap the generated fragment in the xmodule_editor div so that the javascript
    # can bind to it correctly
    component.runtime.wrappers.append(partial(wrap_xblock, handler_prefix))

    try:
        fragment = component.render('studio_view')
    # catch exceptions indiscriminately, since after this point they escape the
    # dungeon and surface as uneditable, unsaveable, and undeletable
    # component-goblins.
    except Exception as exc:                          # pylint: disable=W0703
        fragment = Fragment(render_to_string('html_error.html', {'message': str(exc)}))

    return render_to_response('component.html', {
        'preview': get_preview_fragment(request, component),
        'fragment': fragment
    })


class PreviewModuleSystem(ModuleSystem):  # pylint: disable=abstract-method
    """
    An XModule ModuleSystem for use in Studio previews
    """
    def handler_url(self, block, handler_name, suffix='', query=''):
        return handler_prefix(block, handler_name, suffix) + '?' + query


def preview_module_system(request, descriptor):
    """
    Returns a ModuleSystem for the specified descriptor that is specialized for
    rendering module previews.

    request: The active django request
    descriptor: An XModuleDescriptor
    """

    course_id = get_course_for_item(descriptor.location).location.course_id

    return PreviewModuleSystem(
        static_url=settings.STATIC_URL,
        # TODO (cpennington): Do we want to track how instructors are using the preview problems?
        track_function=lambda event_type, event: None,
        filestore=descriptor.runtime.resources_fs,
        get_module=partial(load_preview_module, request),
        render_template=render_from_lms,
        debug=True,
        replace_urls=partial(static_replace.replace_static_urls, data_directory=None, course_id=course_id),
        user=request.user,
        can_execute_unsafe_code=(lambda: can_execute_unsafe_code(course_id)),
        mixins=settings.XBLOCK_MIXINS,
        course_id=course_id,
        anonymous_student_id='student',

        # Set up functions to modify the fragment produced by student_view
        wrappers=(
            # This wrapper wraps the module in the template specified above
            partial(wrap_xblock, handler_prefix, display_name_only=descriptor.location.category == 'static_tab'),

            # This wrapper replaces urls in the output that start with /static
            # with the correct course-specific url for the static content
            partial(
                replace_static_urls,
                getattr(descriptor, 'data_dir', descriptor.location.course),
                course_id=descriptor.location.org + '/' + descriptor.location.course + '/BOGUS_RUN_REPLACE_WHEN_AVAILABLE',
            ),
        ),
        error_descriptor_class=ErrorDescriptor,
    )


def load_preview_module(request, descriptor):
    """
    Return a preview XModule instantiated from the supplied descriptor.

    request: The active django request
    descriptor: An XModuleDescriptor
    """
    student_data = DbModel(SessionKeyValueStore(request))
    descriptor.bind_for_student(
        preview_module_system(request, descriptor),
        LmsFieldData(descriptor._field_data, student_data),  # pylint: disable=protected-access
    )
    return descriptor


def get_preview_fragment(request, descriptor):
    """
    Returns the HTML returned by the XModule's student_view,
    specified by the descriptor and idx.
    """
    module = load_preview_module(request, descriptor)
    try:
        fragment = module.render("student_view")
    except Exception as exc:                          # pylint: disable=W0703
        fragment = Fragment(render_to_string('html_error.html', {'message': str(exc)}))
    return fragment
