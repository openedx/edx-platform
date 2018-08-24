from django.http import HttpResponse

from opaque_keys.edx.keys import UsageKey
from openedx.core.lib.xblock_runtime.blockstore_kvs import BlockstoreKVS
from openedx.core.lib.xblock_runtime.runtime import XBlockRuntimeSystem
from xblock.exceptions import NoSuchViewError
from xblock.runtime import DictKeyValueStore


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
            authored_data_readonly=True,
        )
    return get_readonly_runtime_system._system


def bundle_unit(request, bundle_slug, olx_path):

    # Temporary:

    unit_key = UsageKey.from_string('block-v1:OpenCraft+B+1+type@drag-and-drop-v2+block@971aadaaaa5a4886b37fee3ced711b30')

    block = get_readonly_runtime_system().get_block(unit_key, user_id=request.user.id)
    try:
        fragment = block.render('author_view')
    except NoSuchViewError:
        fragment = block.render('student_view')

    return HttpResponse("This would load the unit {} from the bundle with slug {} and content: {}".format(
        olx_path, bundle_slug, fragment.content
    ))
