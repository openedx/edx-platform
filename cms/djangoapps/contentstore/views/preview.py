# lint-amnesty, pylint: disable=missing-module-docstring

import logging
from functools import partial

from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseBadRequest
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_exempt
from opaque_keys.edx.keys import UsageKey
from web_fragments.fragment import Fragment
from xblock.django.request import django_to_webob_request, webob_to_django_response
from xblock.exceptions import NoSuchHandlerError
from xblock.runtime import KvsFieldData

from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError, ProcessingError
from xmodule.modulestore.django import XBlockI18nService, modulestore
from xmodule.partitions.partitions_service import PartitionService
from xmodule.services import SettingsService, TeamsConfigurationService
from xmodule.studio_editable import has_author_view
from xmodule.util.sandboxing import SandboxService
from xmodule.util.xmodule_django import add_webpack_to_fragment
from xmodule.x_module import AUTHOR_VIEW, PREVIEW_VIEWS, STUDENT_VIEW, ModuleSystem
from cms.djangoapps.xblock_config.models import StudioConfig
from cms.djangoapps.contentstore.toggles import individualize_anonymous_user_id, ENABLE_COPY_PASTE_FEATURE
from cms.lib.xblock.field_data import CmsFieldData
from common.djangoapps.static_replace.services import ReplaceURLService
from common.djangoapps.static_replace.wrapper import replace_urls_wrapper
from common.djangoapps.student.models import anonymous_id_for_user
from common.djangoapps.edxmako.shortcuts import render_to_string
from common.djangoapps.edxmako.services import MakoService
from common.djangoapps.xblock_django.user_service import DjangoXBlockUserService
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from openedx.core.lib.license import wrap_with_license
from openedx.core.lib.cache_utils import CacheService
from openedx.core.lib.xblock_utils import (
    request_token,
    wrap_fragment,
    wrap_xblock,
    wrap_xblock_aside,
    xblock_local_resource_url
)

from ..utils import get_visibility_partition_info
from .access import get_user_role
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
    instance = _load_preview_block(request, descriptor)

    # Let the module handle the AJAX
    req = django_to_webob_request(request)
    try:
        resp = instance.handle(handler, req, suffix)

    except NoSuchHandlerError:
        log.exception("XBlock %s attempted to access missing handler %r", instance, handler)
        raise Http404  # lint-amnesty, pylint: disable=raise-missing-from

    except NotFoundError:
        log.exception("Module indicating to user that request doesn't exist")
        raise Http404  # lint-amnesty, pylint: disable=raise-missing-from

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
    # xblocks can check for this attribute during rendering to determine if
    # they are being rendered for preview (i.e. in Studio)
    is_author_mode = True

    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        return reverse('preview_handler', kwargs={
            'usage_key_string': str(block.scope_ids.usage_id),
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
            for aside_type in super().applicable_aside_types(block)
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
            if aside_frag.content != '':
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
    rendering block previews.

    request: The active django request
    descriptor: An XModuleDescriptor
    """

    course_id = descriptor.location.course_key
    display_name_only = (descriptor.category == 'static_tab')

    replace_url_service = ReplaceURLService(course_id=course_id)

    wrappers = [
        # This wrapper wraps the block in the template specified above
        partial(
            wrap_xblock,
            'PreviewRuntime',
            display_name_only=display_name_only,
            usage_id_serializer=str,
            request_token=request_token(request)
        ),

        # This wrapper replaces urls in the output that start with /static
        # with the correct course-specific url for the static content
        partial(replace_urls_wrapper, replace_url_service=replace_url_service, static_replace_only=True),
        _studio_wrap_xblock,
    ]

    wrappers_asides = [
        partial(
            wrap_xblock_aside,
            'PreviewRuntime',
            usage_id_serializer=str,
            request_token=request_token(request)
        )
    ]

    mako_service = MakoService(namespace_prefix='lms.')
    if settings.FEATURES.get("LICENSING", False):
        # stick the license wrapper in front
        wrappers.insert(0, partial(wrap_with_license, mako_service=mako_service))

    preview_anonymous_user_id = 'student'
    if individualize_anonymous_user_id(course_id):
        # There are blocks (capa, html, and video) where we do not want to scope
        # the anonymous_user_id to specific courses. These are captured in the
        # block attribute 'requires_per_student_anonymous_id'. Please note,
        # the course_id field in AnynomousUserID model is blank if value is None.
        if getattr(descriptor, 'requires_per_student_anonymous_id', False):
            preview_anonymous_user_id = anonymous_id_for_user(request.user, None)
        else:
            preview_anonymous_user_id = anonymous_id_for_user(request.user, course_id)

    return PreviewModuleSystem(
        get_block=partial(_load_preview_block, request),
        mixins=settings.XBLOCK_MIXINS,

        # Set up functions to modify the fragment produced by student_view
        wrappers=wrappers,
        wrappers_asides=wrappers_asides,
        # Get the raw DescriptorSystem, not the CombinedSystem
        descriptor_runtime=descriptor._runtime,  # pylint: disable=protected-access
        services={
            "field-data": field_data,
            "i18n": XBlockI18nService,
            'mako': mako_service,
            "settings": SettingsService(),
            "user": DjangoXBlockUserService(
                request.user,
                user_role=get_user_role(request.user, course_id),
                anonymous_user_id=preview_anonymous_user_id,
            ),
            "partitions": StudioPartitionService(course_id=course_id),
            "teams_configuration": TeamsConfigurationService(),
            "sandbox": SandboxService(contentstore=contentstore, course_id=course_id),
            "cache": CacheService(cache),
            'replace_urls': replace_url_service
        },
    )


class StudioPartitionService(PartitionService):
    """
    A runtime mixin to allow the display and editing of component visibility based on user partitions.
    """
    def get_user_group_id_for_partition(self, user, user_partition_id):
        """
        Override this method to return None, as the split_test_block calls this
        to determine which group a user should see, but is robust to getting a return
        value of None meaning that all groups should be shown.
        """
        return None


def _load_preview_block(request, descriptor):
    """
    Return a preview XBlock instantiated from the supplied descriptor. Will use mutable fields
    if XBlock supports an author_view. Otherwise, will use immutable fields and student_view.

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
            selected_groups_label = _('Access restricted to: {list_of_groups}').format(list_of_groups=selected_groups_label)  # lint-amnesty, pylint: disable=line-too-long
        course = modulestore().get_course(xblock.location.course_key)
        can_edit = context.get('can_edit', True)
        # Copy-paste is a new feature; while we are beta-testing it, only beta users with the Waffle flag enabled see it
        enable_copy_paste = can_edit and ENABLE_COPY_PASTE_FEATURE.is_enabled()
        template_context = {
            'xblock_context': context,
            'xblock': xblock,
            'show_preview': context.get('show_preview', True),
            'content': frag.content,
            'is_root': is_root,
            'is_reorderable': is_reorderable,
            'can_edit': can_edit,
            'enable_copy_paste': enable_copy_paste,
            'can_edit_visibility': context.get('can_edit_visibility', xblock.scope_ids.usage_id.context_key.is_course),
            'selected_groups_label': selected_groups_label,
            'can_add': context.get('can_add', True),
            'can_move': context.get('can_move', xblock.scope_ids.usage_id.context_key.is_course),
            'language': getattr(course, 'language', None)
        }

        add_webpack_to_fragment(frag, "js/factories/xblock_validation")

        html = render_to_string('studio_xblock_wrapper.html', template_context)
        frag = wrap_fragment(frag, html)
    return frag


def get_preview_fragment(request, descriptor, context):
    """
    Returns the HTML returned by the XModule's student_view or author_view (if available),
    specified by the descriptor and idx.
    """
    block = _load_preview_block(request, descriptor)

    preview_view = AUTHOR_VIEW if has_author_view(block) else STUDENT_VIEW

    try:
        fragment = block.render(preview_view, context)
    except Exception as exc:                          # pylint: disable=broad-except
        log.warning("Unable to render %s for %r", preview_view, block, exc_info=True)
        fragment = Fragment(render_to_string('html_error.html', {'message': str(exc)}))
    return fragment
