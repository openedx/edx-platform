from __future__ import absolute_import, print_function, unicode_literals

from django.http import Http404, JsonResponse

from opaque_keys.edx.keys import UsageKey
from openedx.core.lib.xblock_runtime.blockstore_kvs import BlockstoreKVS, blockstore_transaction
from openedx.core.lib.xblock_runtime.blockstore_runtime import BlockstoreXBlockRuntime
from openedx.core.lib.xblock_runtime.runtime import XBlockRuntimeSystem
from openedx.core.lib.xblock_keys import global_context
from xblock.exceptions import NoSuchViewError, XBlockNotFoundError
from xblock.runtime import DictKeyValueStore

from openedx.core.lib.blockstore_api import get_bundle_by_slug, get_bundle_file_data


def get_blockstore_kvs():
    """
    Get the BlockstoreKVS singleton.

    This key-value store is used by the XBlock runtime's SplitFieldData
    class as the underlying data store for authored data. It reads and
    writes XML data from bundles in blockstore.
    """
    if not hasattr('get_blockstore_kvs', '_kvs'):
        get_blockstore_kvs._kvs = BlockstoreKVS()
    return get_blockstore_kvs._kvs


def get_user_state_kvs():
    """
    Get the key-value store used by the XBlock runtime's SplitFieldData
    class to hold user state.

    This user state is not persisted anywhere.
    """
    if not hasattr('get_user_state_kvs', '_kvs'):
        get_user_state_kvs._kvs = DictKeyValueStore()
    return get_user_state_kvs._kvs


def get_readonly_runtime_system():
    """
    Get the XBlockRuntimeSystem for viewing content in Studio but
    not editing it at the moment
    """
    if not hasattr('get_blockstore_runtime_system', '_system'):
        get_readonly_runtime_system._system = XBlockRuntimeSystem(
            handler_url=lambda *args, **kwargs: 'test_url',  # TODO: Need an actual method for calling handler_urls with this runtime
            authored_data_kvs=get_blockstore_kvs(),
            student_data_kvs=get_user_state_kvs(),
            runtime_class=BlockstoreXBlockRuntime,
        )
    return get_readonly_runtime_system._system


def bundle_unit(request, bundle_slug, olx_path):
    """
    Get the HTML, JS, and CSS needed to render the root XBlock of the given OLX
    file in the Blockstore bundle with the given slug.
    """
    # Find the bundle UUID:
    bundle = get_bundle_by_slug(bundle_slug)
    if not bundle:
        raise Http404("Bundle not found")

    runtime = get_readonly_runtime_system().get_runtime(user_id=request.user.id)
    with blockstore_transaction():
        try:
            unit_key = runtime.parse_olx_file(bundle.uuid, olx_path, context_key=global_context)
        except XBlockNotFoundError:
            raise Http404("OLX file not found")
        block = runtime.get_block(unit_key)
        try:
            fragment = block.render('author_view')
        except NoSuchViewError:
            fragment = block.render('student_view')

    data = {
        "root_usage_key": unicode(unit_key),
    }
    data.update(fragment.to_dict())

    return JsonResponse(data)
