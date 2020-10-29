

import logging
from functools import partial

import six
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.clickjacking import xframe_options_exempt
from opaque_keys.edx.keys import UsageKey
from web_fragments.fragment import Fragment
from xblock.django.request import django_to_webob_request, webob_to_django_response
from xblock.exceptions import NoSuchHandlerError
from xblock.runtime import KvsFieldData

from common.djangoapps import static_replace
from cms.djangoapps.xblock_config.models import StudioConfig
from cms.lib.xblock.field_data import CmsFieldData
from common.djangoapps.edxmako.shortcuts import render_to_string
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from openedx.core.lib.license import wrap_with_license
from openedx.core.lib.xblock_utils import (
    replace_static_urls,
    request_token,
    wrap_fragment,
    wrap_xblock,
    wrap_xblock_aside,
    xblock_local_resource_url
)
from common.djangoapps.xblock_django.user_service import DjangoXBlockUserService
from xmodule.contentstore.django import contentstore
from xmodule.error_module import ErrorDescriptor
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.modulestore.django import ModuleI18nService, modulestore
from xmodule.partitions.partitions_service import PartitionService
from xmodule.services import SettingsService
from xmodule.studio_editable import has_author_view
from xmodule.util.sandboxing import can_execute_unsafe_code, get_python_lib_zip
from xmodule.util.xmodule_django import add_webpack_to_fragment
from xmodule.x_module import AUTHOR_VIEW, PREVIEW_VIEWS, STUDENT_VIEW, ModuleSystem, XModule, XModuleDescriptor

from ..utils import get_visibility_partition_info
from .access import get_user_role
from .helpers import render_from_lms
from .session_kv_store import SessionKeyValueStore

__all__ = ['preview_handler']

log = logging.getLogger(__name__)


@login_required
@xframe_options_exempt
def preview_handler(request, usage_key_string, handler, suffix=''):
    """
    Dispatch an AJAX action to an xblock

    usage_key_string: The usage_key_string-id of the block to dispatch to, passed through `quote_slashes`
    handler: The handler to execute
    suffix: The remainder of the url to be passed to the handler
    """
    usage_key = UsageKey.from_string(usage_key_string)

    descriptor = modulestore().get_item(usage_key)
    instance = _load_preview_module(request, descriptor)

    # Let the module handle the AJAX
    req = django_to_webob_request(request)
    try:
        resp = instance.handle(handler, req, suffix)

    except NoSuchHandlerError:
        log.exception(u"XBlock %s attempted to access missing handler %r", instance, handler)
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


class PreviewModuleSystem(ModuleSystem):  # pylint: disable=abstract-method
    """
    An XModule ModuleSystem for use in Studio previews
    """
    # xmodules can check for this attribute during rendering to determine if
    # they are being rendered for preview (i.e. in Studio)
    is_author_mode = True

    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        return reverse('preview_handler', kwargs={
            'usage_key_string': six.text_type(block.scope_ids.usage_id),
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
        result.add_fragment_resources(frag)

        for aside, aside_fn in aside_frag_fns:
            aside_frag = aside_fn(block, context)
            if aside_frag.content != u'':
                aside_frag_wrapped = self.wrap_aside(block, aside, view_name, aside_frag, context)
                aside.save()
                result.add_fragment_resources(aside_frag_wrapped)
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
            usage_id_serializer=six.text_type,
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
            usage_id_serializer=six.text_type,
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
            "partitions": StudioPartitionService(course_id=course_id)
        },
    )


class StudioPartitionService(PartitionService):
    """
    A runtime mixin to allow the display and editing of component visibility based on user partitions.
    """
    def get_user_group_id_for_partition(self, user, user_partition_id):
        """
        Override this method to return None, as the split_test_module calls this
        to determine which group a user should see, but is robust to getting a return
        value of None meaning that all groups should be shown.
        """
        return None


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
    Returns true if the specified xblock is in the set of reorderable xblocks
    otherwise returns false.
    """
    try:
        return xblock.location in context['reorderable_items']
    except KeyError:
        return False


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
        selected_groups_label = get_visibility_partition_info(xblock)['selected_groups_label']
        if selected_groups_label:
            selected_groups_label = _(u'Access restricted to: {list_of_groups}').format(list_of_groups=selected_groups_label)
        course = modulestore().get_course(xblock.location.course_key)
        template_context = {
            'xblock_context': context,
            'xblock': xblock,
            'show_preview': context.get('show_preview', True),
            'content': frag.content,
            'is_root': is_root,
            'is_reorderable': is_reorderable,
            'can_edit': context.get('can_edit', True),
            'can_edit_visibility': context.get('can_edit_visibility', True),
            'selected_groups_label': selected_groups_label,
            'can_add': context.get('can_add', True),
            'can_move': context.get('can_move', True),
            'language': getattr(course, 'language', None)
        }

        if isinstance(xblock, (XModule, XModuleDescriptor)):
            # Add the webpackified asset tags
            class_name = getattr(xblock.__class__, 'unmixed_class', xblock.__class__).__name__
            add_webpack_to_fragment(frag, class_name)

        add_webpack_to_fragment(frag, "js/factories/xblock_validation")

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
        log.warning(u"Unable to render %s for %r", preview_view, module, exc_info=True)
        fragment = Fragment(render_to_string('html_error.html', {'message': str(exc)}))
    return fragment
