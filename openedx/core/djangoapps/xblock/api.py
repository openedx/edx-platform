"""
Python API for interacting with edx-platform's new XBlock Runtime.

For content in modulestore (currently all course content), you'll need to use
the older runtime.

Note that these views are only for interacting with existing blocks. Other
Studio APIs cover use cases like adding/deleting/editing blocks.
"""
# pylint: disable=unused-import

from datetime import datetime
import logging
import threading

from django.urls import reverse
from django.utils.translation import gettext as _
from openedx_learning.core.components import api as components_api
from openedx_learning.core.publishing import api as publishing_api
from opaque_keys.edx.keys import UsageKeyV2
from opaque_keys.edx.locator import BundleDefinitionLocator, LibraryUsageLocatorV2

from rest_framework.exceptions import NotFound
from xblock.core import XBlock
from xblock.exceptions import NoSuchViewError
from xblock.plugin import PluginMissingError

from openedx.core.djangoapps.xblock.apps import get_xblock_app_config
from openedx.core.djangoapps.xblock.learning_context.manager import get_learning_context_impl

from openedx.core.djangoapps.xblock.runtime.learning_core_runtime import (
    LearningCoreFieldData,
    LearningCoreOpaqueKeyReader,
    LearningCoreXBlockRuntime,
)


from openedx.core.djangoapps.xblock.runtime.runtime import XBlockRuntimeSystem as _XBlockRuntimeSystem
from .utils import get_secure_token_for_xblock_handler, get_xblock_id_for_anonymous_user

# Made available as part of this package's public API:
from openedx.core.djangoapps.xblock.learning_context import LearningContext

# Implementation:

log = logging.getLogger(__name__)


def get_runtime_system():
    """
    Get the XBlockRuntimeSystem, which is a single long-lived factory that can
    create user-specific runtimes.

    The Runtime System isn't always needed (e.g. for management commands), so to
    keep application startup faster, it's only initialized when first accessed
    via this method.
    """
    # TODO: Is any of the following necessary now that we're no longer using
    # Blockstore or its caching mechanisms? And why were we doing a dict with
    # attributes manually set by thread ID instead of a ContextVar?
    #
    # The runtime system should not be shared among threads, as there is currently a race condition when parsing XML
    # that can lead to duplicate children.
    # (In BlockstoreXBlockRuntime.get_block(), has_cached_definition(def_id) returns false so parse_xml is called, but
    # meanwhile another thread parses the XML and caches the definition; then when parse_xml gets to XML nodes for
    # child blocks, it appends them to the children already cached by the other thread and saves the doubled list of
    # children; this happens only occasionally but is very difficult to avoid in a clean way due to the API of parse_xml
    # and XBlock field data in general [does not distinguish between setting initial values during parsing and changing
    # values at runtime due to user interaction], and how it interacts with BlockstoreFieldData. Keeping the caches
    # local to each thread completely avoids this problem.)
    cache_name = f'_system_{threading.get_ident()}'
    if not hasattr(get_runtime_system, cache_name):
        params = dict(
            handler_url=get_handler_url,
            runtime_class=LearningCoreXBlockRuntime,
        )
        params.update(get_xblock_app_config().get_runtime_system_params())
        setattr(get_runtime_system, cache_name, _XBlockRuntimeSystem(**params))
    return getattr(get_runtime_system, cache_name)

def get_runtime_system():
    params = get_xblock_app_config().get_runtime_system_params()
    params.update(
        runtime_class=LearningCoreXBlockRuntime,
        handler_url=get_handler_url,
        authored_data_store=LearningCoreFieldData(),
    )
    start = datetime.now()
    runtime = _XBlockRuntimeSystem(**params)
    end = datetime.now()
    log.info(f"Runtime initiated in {end - start}")

    return runtime

def load_block(usage_key, user):
    """
    Load the specified XBlock for the given user.

    Returns an instantiated XBlock.

    Exceptions:
        NotFound - if the XBlock doesn't exist or if the user doesn't have the
                   necessary permissions

    Args:
        usage_key(OpaqueKey): block identifier
        user(User): user requesting the block
    """
    # Is this block part of a course, a library, or what?
    # Get the Learning Context Implementation based on the usage key
    context_impl = get_learning_context_impl(usage_key)

    log.error(f"load_block using {context_impl} for {usage_key}")

    # Now, check if the block exists in this context and if the user has
    # permission to render this XBlock view:
    if user is not None and not context_impl.can_view_block(user, usage_key):
        # We do not know if the block was not found or if the user doesn't have
        # permission, but we want to return the same result in either case:
        raise NotFound(f"XBlock {usage_key} does not exist, or you don't have permission to view it.")

    # TODO: load field overrides from the context
    # e.g. a course might specify that all 'problem' XBlocks have 'max_attempts'
    # set to 3.
    # field_overrides = context_impl.get_field_overrides(usage_key)

    runtime = get_runtime_system().get_runtime(user=user)

    return runtime.get_block(usage_key)


def get_block_metadata(block, includes=()):
    """
    Get metadata about the specified XBlock.

    This metadata is the same for all users. Any data which varies per-user must
    be served from a different API.

    Optionally provide a list or set of metadata keys to include. Valid keys are:
        index_dictionary: a dictionary of data used to add this XBlock's content
            to a search index.
        student_view_data: data needed to render the XBlock on mobile or in
            custom frontends.
        children: list of usage keys of the XBlock's children
        editable_children: children in the same bundle, as opposed to linked
            children in other bundles.
    """
    data = {
        "block_id": str(block.scope_ids.usage_id),
        "block_type": block.scope_ids.block_type,
        "display_name": get_block_display_name(block),
    }

    if "index_dictionary" in includes:
        data["index_dictionary"] = block.index_dictionary()

    if "student_view_data" in includes:
        data["student_view_data"] = block.student_view_data() if hasattr(block, 'student_view_data') else None

    if "children" in includes:
        data["children"] = block.children if hasattr(block, 'children') else []  # List of usage keys of children

    if "editable_children" in includes:
        # "Editable children" means children in the same bundle, as opposed to linked children in other bundles.
        data["editable_children"] = []
        child_includes = block.runtime.child_includes_of(block)
        for idx, include in enumerate(child_includes):
            if include.link_id is None:
                data["editable_children"].append(block.children[idx])

    return data


def resolve_definition(block_or_key):
    """
    Given an XBlock, definition key, or usage key, return the definition key.
    """
    if isinstance(block_or_key, BundleDefinitionLocator):
        return block_or_key
    elif isinstance(block_or_key, UsageKeyV2):
        context_impl = get_learning_context_impl(block_or_key)
        return context_impl.definition_for_usage(block_or_key)
    elif isinstance(block_or_key, XBlock):
        return block_or_key.scope_ids.def_id
    else:
        raise TypeError(block_or_key)


def xblock_type_display_name(block_type):
    """
    Get the display name for the specified XBlock class.
    """
    try:
        # We want to be able to give *some* value, even if the XBlock is later
        # uninstalled.
        block_class = XBlock.load_class(block_type)
    except PluginMissingError:
        return block_type

    if hasattr(block_class, 'display_name') and block_class.display_name.default:
        return _(block_class.display_name.default)  # pylint: disable=translation-of-non-string
    else:
        return block_type  # Just use the block type as the name


def _get_component_from_usage_key(usage_key):
    learning_package = publishing_api.get_learning_package_by_key(str(usage_key.lib_key))
    return components_api.get_component_by_key(
        learning_package.id,
        namespace='xblock.v1',
        type_name=usage_key.block_type,
        local_key=usage_key.block_id,
    )

def get_library_block_olx(usage_key: LibraryUsageLocatorV2):
    """
    Get the OLX source of the given XBlock.
    """
    # Inefficient but simple approach first
    component = _get_component_from_usage_key(usage_key)
    component_version = component.versioning.draft

    # TODO: we should probably make a method on ComponentVersion that returns
    # a content based on the name.
    content = component_version.contents.get(componentversioncontent__key="block.xml")

    return content.text


def get_block_display_name(block_or_key):
    if isinstance(block_or_key, XBlock):
        return block_or_key.display_name
    elif isinstance(block_or_key, UsageKeyV2):
        component = _get_component_from_usage_key(block_or_key)
        return component.draft.title if component.draft else ""

    raise TypeError(
        "display_name lookup expects a UsageKeyV2 or XBlock, " +
        f"got {type(block_or_key)}: {block_or_key} instead"
    )


def render_block_view(block, view_name, user):  # pylint: disable=unused-argument
    """
    Get the HTML, JS, and CSS needed to render the given XBlock view.

    The only difference between this method and calling
        load_block().render(view_name)
    is that this method can fall back from 'author_view' to 'student_view'

    Returns a Fragment.
    """
    try:
        fragment = block.render(view_name)
    except NoSuchViewError:
        fallback_view = None
        if view_name == 'author_view':
            fallback_view = 'student_view'
        if fallback_view:
            fragment = block.render(fallback_view)
        else:
            raise

    return fragment


def get_handler_url(usage_key, handler_name, user):
    """
    A method for getting the URL to any XBlock handler. The URL must be usable
    without any authentication (no cookie, no OAuth/JWT), and may expire. (So
    that we can render the XBlock in a secure IFrame without any access to
    existing cookies.)

    The returned URL will contain the provided handler_name, but is valid for
    any other handler on the same XBlock. Callers may replace any occurrences of
    the handler name in the resulting URL with the name of any other handler and
    the URL will still work. (This greatly reduces the number of calls to this
    API endpoint that are needed to interact with any given XBlock.)

    Params:
        usage_key       - Usage Key (Opaque Key object or string)
        handler_name    - Name of the handler or a dummy name like 'any_handler'
        user            - Django User (registered or anonymous)

    This view does not check/care if the XBlock actually exists.
    """
    usage_key_str = str(usage_key)
    site_root_url = get_xblock_app_config().get_site_root_url()
    if not user:  # lint-amnesty, pylint: disable=no-else-raise
        raise TypeError("Cannot get handler URLs without specifying a specific user ID.")
    elif user.is_authenticated:
        user_id = user.id
    elif user.is_anonymous:
        user_id = get_xblock_id_for_anonymous_user(user)
    else:
        raise ValueError("Invalid user value")
    # Now generate a token-secured URL for this handler, specific to this user
    # and this XBlock:
    secure_token = get_secure_token_for_xblock_handler(user_id, usage_key_str)
    # Now generate the URL to that handler:
    path = reverse('xblock_api:xblock_handler', kwargs={
        'usage_key_str': usage_key_str,
        'user_id': user_id,
        'secure_token': secure_token,
        'handler_name': handler_name,
    })
    # We must return an absolute URL. We can't just use
    # rest_framework.reverse.reverse to get the absolute URL because this method
    # can be called by the XBlock from python as well and in that case we don't
    # have access to the request.
    return site_root_url + path
