from __future__ import absolute_import

import logging
from functools import partial

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from edxmako.shortcuts import render_to_string

from openedx.core.lib.xblock_utils import (
    replace_static_urls, wrap_xblock, wrap_fragment, wrap_xblock_aside, request_token, xblock_local_resource_url,
)
from xmodule.x_module import PREVIEW_VIEWS, STUDENT_VIEW, AUTHOR_VIEW
from xmodule.contentstore.django import contentstore
from xmodule.error_module import ErrorDescriptor
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.studio_editable import has_author_view
from xmodule.services import SettingsService
from xmodule.modulestore.django import modulestore, ModuleI18nService
from xmodule.mixin import wrap_with_license
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.asides import AsideUsageKeyV1
from xmodule.x_module import ModuleSystem
from xblock.runtime import KvsFieldData
from xblock.django.request import webob_to_django_response, django_to_webob_request
from xblock.exceptions import NoSuchHandlerError
from xblock.fragment import Fragment
from student.auth import has_studio_read_access, has_studio_write_access
from xblock_django.user_service import DjangoXBlockUserService

from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from cms.lib.xblock.field_data import CmsFieldData

from util.sandboxing import can_execute_unsafe_code, get_python_lib_zip

import static_replace
from .session_kv_store import SessionKeyValueStore
from .helpers import render_from_lms

from contentstore.views.access import get_user_role
from xblock_config.models import StudioConfig

__all__ = ['preview_handler']

log = logging.getLogger(__name__)


@login_required
def preview_handler(request, usage_key_string, handler, suffix=''):
    """
    Dispatch an AJAX action to an xblock

    usage_key_string: The usage_key_string-id of the block to dispatch to, passed through `quote_slashes`
    handler: The handler to execute
    suffix: The remainder of the url to be passed to the handler
    """
    usage_key = UsageKey.from_string(usage_key_string)

    if isinstance(usage_key, AsideUsageKeyV1):
        descriptor = modulestore().get_item(usage_key.usage_key)
        for aside in descriptor.runtime.get_asides(descriptor):
            if aside.scope_ids.block_type == usage_key.aside_type:
                asides = [aside]
                instance = aside
                break
    else:
        descriptor = modulestore().get_item(usage_key)
        instance = _load_preview_module(request, descriptor)
        asides = []

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

    modulestore().update_item(descriptor, request.user.id, asides=asides)
    return webob_to_django_response(resp)


class PreviewModuleSystem(ModuleSystem):  # pylint: disable=abstract-method
    """
    An XModule ModuleSystem for use in Studio previews
    """
    # xmodules can check for this attribute during rendering to determine if
    # they are being rendered for preview (i.e. in Studio)
    is_author_mode = True

    def __init__(self, **kwargs):
        super(PreviewModuleSystem, self).__init__(**kwargs)

    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        return reverse('preview_handler', kwargs={
            'usage_key_string': unicode(block.scope_ids.usage_id),
            'handler': handler_name,
            'suffix': suffix,
        }) + '?' + query

    def local_resource_url(self, block, uri):
        return xblock_local_resource_url(block, uri)

    def applicable_aside_types(self, block):
        """
        Remove acid_aside and honor the config record
        """
        if not StudioConfig.asides_enabled(block.scope_ids.block_type):
            return []

        # TODO: aside_type != 'acid_aside' check should be removed once AcidBlock is only installed during tests
        # (see https://openedx.atlassian.net/browse/TE-811)
        return [
            aside_type
            for aside_type in super(PreviewModuleSystem, self).applicable_aside_types(block)
            if aside_type != 'acid_aside'
        ]

    def render_child_placeholder(self, block, view_name, context):
        """
        Renders a placeholder XBlock.
        """
        return self.wrap_xblock(block, view_name, Fragment(), context)

    def layout_asides(self, block, context, frag, view_name, aside_frag_fns):
        position_for_asides = '<!-- footer for xblock_aside -->'
        result = Fragment()
        result.add_frag_resources(frag)

        for aside, aside_fn in aside_frag_fns:
            aside_frag = aside_fn(block, context)
            if aside_frag.content != u'':
                aside_frag_wrapped = self.wrap_aside(block, aside, view_name, aside_frag, context)
                aside.save()
                result.add_frag_resources(aside_frag_wrapped)
                replacement = position_for_asides + aside_frag_wrapped.content
                frag.content = frag.content.replace(position_for_asides, replacement)

        result.add_content(frag.content)
        return result


def _preview_module_system(request, descriptor, field_data):
    """
    Returns a ModuleSystem for the specified descriptor that is specialized for
    rendering module previews.

    request: The active django request
    descriptor: An XModuleDescriptor
    """

    course_id = descriptor.location.course_key
    display_name_only = (descriptor.category == 'static_tab')

    wrappers = [
        # This wrapper wraps the module in the template specified above
        partial(
            wrap_xblock,
            'PreviewRuntime',
            display_name_only=display_name_only,
            usage_id_serializer=unicode,
            request_token=request_token(request)
        ),

        # This wrapper replaces urls in the output that start with /static
        # with the correct course-specific url for the static content
        partial(replace_static_urls, None, course_id=course_id),
        _studio_wrap_xblock,
    ]

    wrappers_asides = [
        partial(
            wrap_xblock_aside,
            'PreviewRuntime',
            usage_id_serializer=unicode,
            request_token=request_token(request)
        )
    ]

    if settings.FEATURES.get("LICENSING", False):
        # stick the license wrapper in front
        wrappers.insert(0, wrap_with_license)

    return PreviewModuleSystem(
        static_url=settings.STATIC_URL,
        # TODO (cpennington): Do we want to track how instructors are using the preview problems?
        track_function=lambda event_type, event: None,
        filestore=descriptor.runtime.resources_fs,
        get_module=partial(_load_preview_module, request),
        render_template=render_from_lms,
        debug=True,
        replace_urls=partial(static_replace.replace_static_urls, data_directory=None, course_id=course_id),
        user=request.user,
        can_execute_unsafe_code=(lambda: can_execute_unsafe_code(course_id)),
        get_python_lib_zip=(lambda: get_python_lib_zip(contentstore, course_id)),
        mixins=settings.XBLOCK_MIXINS,
        course_id=course_id,
        anonymous_student_id='student',

        # Set up functions to modify the fragment produced by student_view
        wrappers=wrappers,
        wrappers_asides=wrappers_asides,
        error_descriptor_class=ErrorDescriptor,
        get_user_role=lambda: get_user_role(request.user, course_id),
        # Get the raw DescriptorSystem, not the CombinedSystem
        descriptor_runtime=descriptor._runtime,  # pylint: disable=protected-access
        services={
            "field-data": field_data,
            "i18n": ModuleI18nService,
            "settings": SettingsService(),
            "user": DjangoXBlockUserService(request.user),
        },
    )


def _load_preview_module(request, descriptor):
    """
    Return a preview XModule instantiated from the supplied descriptor. Will use mutable fields
    if XModule supports an author_view. Otherwise, will use immutable fields and student_view.

    request: The active django request
    descriptor: An XModuleDescriptor
    """
    student_data = KvsFieldData(SessionKeyValueStore(request))
    if has_author_view(descriptor):
        wrapper = partial(CmsFieldData, student_data=student_data)
    else:
        wrapper = partial(LmsFieldData, student_data=student_data)

    # wrap the _field_data upfront to pass to _preview_module_system
    wrapped_field_data = wrapper(descriptor._field_data)  # pylint: disable=protected-access
    preview_runtime = _preview_module_system(request, descriptor, wrapped_field_data)

    descriptor.bind_for_student(
        preview_runtime,
        request.user.id,
        [wrapper]
    )
    return descriptor


def _is_xblock_reorderable(xblock, context):
    """
    Returns true if the specified xblock is in the set of reorderable xblocks.
    """
    return xblock.location in context['reorderable_items']


# pylint: disable=unused-argument
def _studio_wrap_xblock(xblock, view, frag, context, display_name_only=False):
    """
    Wraps the results of rendering an XBlock view in a div which adds a header and Studio action buttons.
    """
    # Only add the Studio wrapper when on the container page. The "Pages" page will remain as is for now.
    if not context.get('is_pages_view', None) and view in PREVIEW_VIEWS:
        root_xblock = context.get('root_xblock')
        is_root = root_xblock and xblock.location == root_xblock.location
        is_reorderable = _is_xblock_reorderable(xblock, context)
        template_context = {
            'xblock_context': context,
            'xblock': xblock,
            'show_preview': context.get('show_preview', True),
            'content': frag.content,
            'is_root': is_root,
            'is_reorderable': is_reorderable,
            'can_edit': context.get('can_edit', True),
            'can_edit_visibility': context.get('can_edit_visibility', True),
            'can_add': context.get('can_add', True),
        }
        html = render_to_string('studio_xblock_wrapper.html', template_context)
        frag = wrap_fragment(frag, html)
    return frag


def get_preview_fragment(request, descriptor, context):
    """
    Returns the HTML returned by the XModule's student_view or author_view (if available),
    specified by the descriptor and idx.
    """
    module = _load_preview_module(request, descriptor)

    preview_view = AUTHOR_VIEW if has_author_view(module) else STUDENT_VIEW

    try:
        fragment = module.render(preview_view, context)
    except Exception as exc:                          # pylint: disable=broad-except
        log.warning("Unable to render %s for %r", preview_view, module, exc_info=True)
        fragment = Fragment(render_to_string('html_error.html', {'message': str(exc)}))
    return fragment
