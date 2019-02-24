"""
Views for dealing with XBlocks that are in a Blockstore bundle.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from uuid import UUID

from django.conf import settings
from django.http import Http404, JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework.response import Response
from rest_framework.reverse import reverse as drf_reverse
import six
from xblock.django.request import DjangoWebobRequest, webob_to_django_response
from xblock.exceptions import NoSuchViewError
from xblock.runtime import DictKeyValueStore

from opaque_keys.edx.keys import UsageKey
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.lib.blockstore_api import get_bundle, list_olx_definitions
from openedx.core.lib.xblock_runtime.blockstore_kvs import BlockstoreKVS, blockstore_transaction, collect_changes
from openedx.core.lib.xblock_runtime.blockstore_runtime import BlockstoreXBlockRuntime
from openedx.core.lib.xblock_runtime.runtime import XBlockRuntimeSystem
from openedx.core.lib.xblock_runtime.utils import (
    get_secure_token_for_xblock_handler,
    validate_secure_token_for_xblock_handler,
)
from openedx.core.lib.xblock_keys import global_context, BundleDefinitionLocator


def get_blockstore_kvs():
    """
    Get the BlockstoreKVS singleton.

    This key-value store is used by the XBlock runtime's SplitFieldData
    class as the underlying data store for authored data. It reads and
    writes XML data from bundles in blockstore.
    """
    # pylint: disable=protected-access
    if not hasattr(get_blockstore_kvs, '_kvs'):
        get_blockstore_kvs._kvs = BlockstoreKVS()
    return get_blockstore_kvs._kvs


def get_user_state_kvs():
    """
    Get the key-value store used by the XBlock runtime's SplitFieldData
    class to hold user state.

    This user state is not persisted anywhere.
    """
    # pylint: disable=protected-access
    if not hasattr(get_user_state_kvs, '_kvs'):
        get_user_state_kvs._kvs = DictKeyValueStore()
    return get_user_state_kvs._kvs


def get_xblock_handler_url(usage_id_str, handler_name, suffix, user_id):
    """
    Studio's implementation of a method for getting the URL to any XBlock
    handler. The URL must be usable without any authentication (no cookie,
    no OAuth/JWT), and may expire.
    """
    scheme = "https" if settings.HTTPS == "on" else "http"
    site_root_url = scheme + '://' + settings.CMS_BASE
    # or for the LMS version: configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)

    if user_id == XBlockRuntimeSystem.ANONYMOUS_USER:
        raise NotImplementedError("thirdparty handler links not yet implemented")  # TODO: implement
    else:
        # Normal case: generate a token-secured URL for this handler, specific
        # to this user and this XBlock.
        secure_token = get_secure_token_for_xblock_handler(user_id, usage_id_str)
        path = reverse('bundle_xblock_handler', kwargs={
            'usage_key_str': usage_id_str,
            'user_id': user_id,
            'secure_token': secure_token,
            'handler_name': handler_name,
        })
    return site_root_url + path


def get_readonly_runtime_system():
    """
    Get the XBlockRuntimeSystem for viewing content in Studio but
    not editing it at the moment
    """
    # pylint: disable=protected-access
    if not hasattr(get_readonly_runtime_system, '_system'):
        get_readonly_runtime_system._system = XBlockRuntimeSystem(
            handler_url=get_xblock_handler_url,
            authored_data_kvs=get_blockstore_kvs(),
            student_data_kvs=get_user_state_kvs(),
            runtime_class=BlockstoreXBlockRuntime,
        )
    return get_readonly_runtime_system._system


def bundle_blocks(request, bundle_uuid_str):
    """
    List all the block definitions in the specified bundle.
    """
    bundle_uuid = UUID(bundle_uuid_str)
    bundle = get_bundle(bundle_uuid)
    if bundle is None:
        raise Http404("Bundle not found")

    data = list_olx_definitions(bundle_uuid)
    result = []
    for path, entries in six.viewitems(data):
        blocks = []
        for (block_type, definition_id) in entries:
            definition_key = BundleDefinitionLocator(
                bundle_uuid=bundle_uuid, block_type=block_type, definition_id=definition_id,
            )
            usage_key = global_context.make_usage_key(definition_key)
            blocks.append({
                "definition_key": six.text_type(definition_key),
                "url": request.build_absolute_uri(
                    reverse(bundle_block, kwargs={'usage_key_str': six.text_type(usage_key)})
                ),
            })
        result.append({
            "path": path,
            "blocks": blocks,
        })
    return JsonResponse({"bundle_files": result})


def bundle_block(request, usage_key_str, view_name='student_view'):
    """
    Get the HTML, JS, and CSS needed to render the given XBlock
    in the global learning context
    """
    usage_key = UsageKey.from_string(usage_key_str)
    if usage_key.context_key != global_context:
        return HttpResponseBadRequest("This API method only works with usages in the global context.")

    fallback_view = None
    if view_name == 'author_view':
        fallback_view = 'student_view'

    runtime = get_readonly_runtime_system().get_runtime(user_id=request.user.id)
    with blockstore_transaction():
        block = runtime.get_block(usage_key)
        try:
            fragment = block.render(view_name)
        except NoSuchViewError:
            if fallback_view:
                fragment = block.render('student_view')
            else:
                raise

    data = {
        "usage_key": six.text_type(usage_key),
    }
    data.update(fragment.to_dict())

    return JsonResponse(data)


@api_view(['GET'])
@view_auth_classes(is_authenticated=True)
def bundle_xblock_handler_url(request, usage_key_str, handler_name):
    """
    Get an absolute URL which can be used (without any authentication) to call
    the given XBlock handler.
    
    The URL will expire but is guaranteed to be valid for a minimum of 2 days.
    """
    handler_url = get_xblock_handler_url(usage_key_str, handler_name, '', request.user.id)
    return Response({"handler_url": handler_url})


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@authentication_classes([])  # Disable session authentication; we don't need it and don't want CSRF checks
@permission_classes((permissions.AllowAny, ))
def bundle_xblock_handler(request, user_id, secure_token, usage_key_str, handler_name, suffix):
    """
    Run an XBlock's handler and return the result
    """
    user_id = int(user_id)  # User ID comes from the URL, not session auth

    usage_key = UsageKey.from_string(usage_key_str)
    if usage_key.context_key != global_context:
        return HttpResponseBadRequest("This API method only works with usages in the global context.")

    runtime = get_readonly_runtime_system().get_runtime(user_id=user_id)

    # To support sandboxed XBlocks, custom frontends, and other use cases, we
    # authenticate requests using a secure token in the URL. see
    # openedx.core.lib.xblock_runtime.runtime.get_secure_hash_for_xblock_handler
    # for details and rationale.
    if not validate_secure_token_for_xblock_handler(user_id, usage_key_str, secure_token):
        raise PermissionDenied("Invalid/expired auth token.")
    if request.user.is_authenticated:
        # The user authenticated twice, e.g. with session auth and the token
        # So just make sure the session auth matches the token
        if request.user.id != user_id:
            raise AuthenticationFailed("Authentication conflict.")

    request_webob = DjangoWebobRequest(request)  # Convert from django request to the webob format that XBlocks expect

    with blockstore_transaction():
        # Load the XBlock:
        block = runtime.get_block(usage_key)
        # Run the handler, and save any resulting XBlock field value changes:
        with collect_changes():
            response_webob = block.handle(handler_name, request_webob, suffix)

    response = webob_to_django_response(response_webob)
    # We need to set Access-Control-Allow-Origin: * to allow sandboxed XBlocks
    # to call these handlers:
    response['Access-Control-Allow-Origin'] = '*'
    return response
