import logging
import sys
from functools import partial

from django.http import HttpResponse, Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response

from xmodule_modifiers import replace_static_urls, wrap_xmodule
from xmodule.error_module import ErrorDescriptor
from xmodule.errortracker import exc_info_to_str
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.mongo import MongoUsage
from xmodule.x_module import ModuleSystem
from xblock.runtime import DbModel

import static_replace
from .session_kv_store import SessionKeyValueStore
from .requests import render_from_lms
from .access import has_access

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
    # TODO (vshnayder): change name from id to location in coffee+html as well.
    if not has_access(request.user, location):
        raise HttpResponseForbidden()

    component = modulestore().get_item(location)

    return render_to_response('component.html', {
        'preview': get_module_previews(request, component)[0],
        'editor': wrap_xmodule(component.get_html, component, 'xmodule_edit.html')(),
    })


def preview_module_system(request, preview_id, descriptor):
    """
    Returns a ModuleSystem for the specified descriptor that is specialized for
    rendering module previews.

    request: The active django request
    preview_id (str): An identifier specifying which preview this module is used for
    descriptor: An XModuleDescriptor
    """

    def preview_model_data(descriptor):
        return DbModel(
            SessionKeyValueStore(request, descriptor._model_data),
            descriptor.module_class,
            preview_id,
            MongoUsage(preview_id, descriptor.location.url()),
        )

    return ModuleSystem(
        ajax_url=reverse('preview_dispatch', args=[preview_id, descriptor.location.url(), '']).rstrip('/'),
        # TODO (cpennington): Do we want to track how instructors are using the preview problems?
        track_function=lambda event_type, event: None,
        filestore=descriptor.system.resources_fs,
        get_module=partial(get_preview_module, request, preview_id),
        render_template=render_from_lms,
        debug=True,
        replace_urls=partial(static_replace.replace_static_urls, data_directory=None, course_namespace=descriptor.location),
        user=request.user,
        xblock_model_data=preview_model_data,
    )


def get_preview_module(request, preview_id, descriptor):
    """
    Returns a preview XModule at the specified location. The preview_data is chosen arbitrarily
    from the set of preview data for the descriptor specified by Location

    request: The active django request
    preview_id (str): An identifier specifying which preview this module is used for
    location: A Location
    """

    return load_preview_module(request, preview_id, descriptor)


def load_preview_module(request, preview_id, descriptor):
    """
    Return a preview XModule instantiated from the supplied descriptor, instance_state, and shared_state

    request: The active django request
    preview_id (str): An identifier specifying which preview this module is used for
    descriptor: An XModuleDescriptor
    instance_state: An instance state string
    shared_state: A shared state string
    """
    system = preview_module_system(request, preview_id, descriptor)
    try:
        module = descriptor.xmodule(system)
    except:
        log.debug("Unable to load preview module", exc_info=True)
        module = ErrorDescriptor.from_descriptor(
            descriptor,
            error_msg=exc_info_to_str(sys.exc_info())
        ).xmodule(system)

    # cdodge: Special case
    if module.location.category == 'static_tab':
        module.get_html = wrap_xmodule(
            module.get_html,
            module,
            "xmodule_tab_display.html",
        )
    else:
        module.get_html = wrap_xmodule(
            module.get_html,
            module,
            "xmodule_display.html",
        )

    module.get_html = replace_static_urls(
        module.get_html,
        getattr(module, 'data_dir', module.location.course),
        course_namespace=Location([module.location.tag, module.location.org, module.location.course, None, None])
    )

    return module


def get_module_previews(request, descriptor):
    """
    Returns a list of preview XModule html contents. One preview is returned for each
    pair of states returned by get_sample_state() for the supplied descriptor.

    descriptor: An XModuleDescriptor
    """
    preview_html = []
    for idx, (_instance_state, _shared_state) in enumerate(descriptor.get_sample_state()):
        module = load_preview_module(request, str(idx), descriptor)
        preview_html.append(module.get_html())
    return preview_html
