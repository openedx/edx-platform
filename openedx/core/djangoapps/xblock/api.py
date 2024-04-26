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
from openedx_learning.core.components.models import Component
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
    LearningCoreXBlockRuntime,
)


from openedx.core.djangoapps.xblock.runtime.runtime import XBlockRuntimeSystem as _XBlockRuntimeSystem
from .utils import get_secure_token_for_xblock_handler, get_xblock_id_for_anonymous_user

from .runtime.learning_core_runtime import LearningCoreXBlockRuntime

# Made available as part of this package's public API:
from openedx.core.djangoapps.xblock.learning_context import LearningContext

# Implementation:

log = logging.getLogger(__name__)


def get_runtime_system():
    """
    Return a new XBlockRuntimeSystem.

    TODO: Refactor to get rid of the XBlockRuntimeSystem entirely and just
    create the LearningCoreXBlockRuntime and return it. We used to want to keep
    around a long lived runtime system (a factory that returns runtimes) for
    caching purposes, and have it dynamically construct a runtime on request.
    Now we're just re-constructing both the system and the runtime in this call
    and returning it every time, because:

    1. We no longer have slow, Blockstore-style definitions to cache, so the
       performance of this is perfectly acceptable.
    2. Having a singleton increases complexity and the chance of bugs.
    3. Creating the XBlockRuntimeSystem every time only takes about 10-30 µs.

    Given that, the extra XBlockRuntimeSystem class just adds confusion. But
    despite that, it's tested, working code, and so I'm putting off refactoring
    for now.
    """
    params = get_xblock_app_config().get_runtime_system_params()
    params.update(
        runtime_class=LearningCoreXBlockRuntime,
        handler_url=get_handler_url,
        authored_data_store=LearningCoreFieldData(),
    )
    runtime = _XBlockRuntimeSystem(**params)

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


def get_block_display_name(block: XBlock) -> str:
    """
    Get the display name from an instatiated XBlock, falling back to the XBlock-type-defined-default.
    """
    display_name = getattr(block, "display_name", None)
    if display_name is not None:
        return display_name
    else:
        return xblock_type_display_name(block.scope_ids.block_type)


def get_component_from_usage_key(usage_key: UsageKeyV2) -> Component:
    """
    Fetch the Component object for a given usage key.

    Raises a ObjectDoesNotExist error if no such Component exists.

    This is a lower-level function that will return a Component even if there is
    no current draft version of that Component (because it's been soft-deleted).
    """
    learning_package = publishing_api.get_learning_package_by_key(
        str(usage_key.context_key)
    )
    return components_api.get_component_by_key(
        learning_package.id,
        namespace='xblock.v1',
        type_name=usage_key.block_type,
        local_key=usage_key.block_id,
    )


def get_block_draft_olx(usage_key: UsageKeyV2) -> str:
    """
    Get the OLX source of the draft version of the given Learning-Core-backed XBlock.
    """
    # Inefficient but simple approach. Optimize later if needed.
    component = get_component_from_usage_key(usage_key)
    component_version = component.versioning.draft

    # TODO: we should probably make a method on ComponentVersion that returns
    # a content based on the name. Accessing by componentversioncontent__key is
    # awkward.
    content = component_version.contents.get(componentversioncontent__key="block.xml")

    return content.text


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
