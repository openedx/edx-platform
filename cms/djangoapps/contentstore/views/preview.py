import logging
import sys
from functools import partial

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response, render_to_string

from xmodule_modifiers import replace_static_urls, wrap_xblock
from xmodule.error_module import ErrorDescriptor
from xmodule.errortracker import exc_info_to_str
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.modulestore.django import modulestore
from xmodule.x_module import ModuleSystem
from xblock.runtime import DbModel

from lms.xblock.field_data import LmsFieldData

from util.sandboxing import can_execute_unsafe_code

import static_replace
from .session_kv_store import SessionKeyValueStore
from .helpers import render_from_lms
from .access import has_access
from ..utils import get_course_for_item

__all__ = ['preview_dispatch', 'preview_component']

log = logging.getLogger(__name__)


@login_required
def preview_dispatch(request, preview_id, location, dispatch=None):
    """
    Dispatch an AJAX action to a preview XModule

    Expects a POST request, and passes the arguments to the module

    preview_id (str): An identifier specifying which preview this module is used for
    location: The Location of the module to dispatch to
    dispatch: The action to execute
    """

    descriptor = modulestore().get_item(location)
    instance = load_preview_module(request, preview_id, descriptor)
    # Let the module handle the AJAX
    try:
        ajax_return = instance.handle_ajax(dispatch, request.POST)
        # Save any module data that has changed to the underlying KeyValueStore
        instance.save()

    except NotFoundError:
        log.exception("Module indicating to user that request doesn't exist")
        raise Http404

    except ProcessingError:
        log.warning("Module raised an error while processing AJAX request",
                    exc_info=True)
        return HttpResponseBadRequest()

    except:
        log.exception("error processing ajax call")
        raise

    return HttpResponse(ajax_return)


@login_required
def preview_component(request, location):
    "Return the HTML preview of a component"
    # TODO (vshnayder): change name from id to location in coffee+html as well.
    if not has_access(request.user, location):
        return HttpResponseForbidden()

    component = modulestore().get_item(location)
    # Wrap the generated fragment in the xmodule_editor div so that the javascript
    # can bind to it correctly
    component.runtime.wrappers.append(wrap_xblock)

    try:
        content = component.render('studio_view').content
    # catch exceptions indiscriminately, since after this point they escape the
    # dungeon and surface as uneditable, unsaveable, and undeletable
    # component-goblins.
    except Exception as exc:                          # pylint: disable=W0703
        content = render_to_string('html_error.html', {'message': str(exc)})

    return render_to_response('component.html', {
        'preview': get_preview_html(request, component, 0),
        'editor': content
    })


def preview_module_system(request, preview_id, descriptor):
    """
    Returns a ModuleSystem for the specified descriptor that is specialized for
    rendering module previews.

    request: The active django request
    preview_id (str): An identifier specifying which preview this module is used for
    descriptor: An XModuleDescriptor
    """

    course_id = get_course_for_item(descriptor.location).location.course_id

    return ModuleSystem(
        static_url=settings.STATIC_URL,
        ajax_url=reverse('preview_dispatch', args=[preview_id, descriptor.location.url(), '']).rstrip('/'),
        # TODO (cpennington): Do we want to track how instructors are using the preview problems?
        track_function=lambda event_type, event: None,
        filestore=descriptor.runtime.resources_fs,
        get_module=partial(load_preview_module, request, preview_id),
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
            partial(wrap_xblock, display_name_only=descriptor.location.category == 'static_tab'),

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


def load_preview_module(request, preview_id, descriptor):
    """
    Return a preview XModule instantiated from the supplied descriptor.

    request: The active django request
    preview_id (str): An identifier specifying which preview this module is used for
    descriptor: An XModuleDescriptor
    """
    student_data = DbModel(SessionKeyValueStore(request))
    descriptor.bind_for_student(
        preview_module_system(request, preview_id, descriptor),
        LmsFieldData(descriptor._field_data, student_data),  # pylint: disable=protected-access
    )
    return descriptor


def get_preview_html(request, descriptor, idx):
    """
    Returns the HTML returned by the XModule's student_view,
    specified by the descriptor and idx.
    """
    module = load_preview_module(request, str(idx), descriptor)
    try:
        content = module.render("student_view").content
    except Exception as exc:                          # pylint: disable=W0703
        content = render_to_string('html_error.html', {'message': str(exc)})
    return content
