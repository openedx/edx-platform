"""
Views that implement a RESTful API for interacting with XBlocks.

Note that these views are only for interacting with existing blocks. Other
Studio APIs cover use cases like adding/deleting/editing blocks.
"""

from corsheaders.signals import check_request_enabled
from django.contrib.auth import get_user_model
from django.http import Http404
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes  # lint-amnesty, pylint: disable=unused-import
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed, NotFound
from rest_framework.response import Response
from xblock.django.request import DjangoWebobRequest, webob_to_django_response

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from openedx.core.lib.api.view_utils import view_auth_classes
from ..api import (
    get_block_metadata,
    get_handler_url as _get_handler_url,
    load_block,
    render_block_view as _render_block_view,
)
from ..utils import validate_secure_token_for_xblock_handler

User = get_user_model()

LX_BLOCK_TYPES_OVERRIDE = {
    'problem': 'lx_question',
    'video': 'lx_video',
    'html': 'lx_html',
}


invalid_not_found_fmt = "XBlock {usage_key} does not exist, or you don't have permission to view it."


def _block_type_overrides(request_args):
    """
    If the request contains the argument `lx_block_types=1`, then
    returns a dict of LabXchange block types, which override the default block types.

    Otherwise, returns None.

    FYI: This is a temporary change, added to assist LabXchange with the transition to using their custom runtime.
    """
    if request_args.get('lx_block_types'):
        return LX_BLOCK_TYPES_OVERRIDE
    return None


@api_view(['GET'])
@view_auth_classes(is_authenticated=False)
@permission_classes((permissions.AllowAny, ))  # Permissions are handled at a lower level, by the learning context
def block_metadata(request, usage_key_str):
    """
    Get metadata about the specified block.

    Accepts the following query parameters:

    * "include": a comma-separated list of keys to include.
      Valid keys are "index_dictionary" and "student_view_data".
    * "lx_block_types": optional boolean; set to use the LabXchange XBlock classes to load the requested block.
      The block ID and OLX remain unchanged; they will use the original block type.
    """
    try:
        usage_key = UsageKey.from_string(usage_key_str)
    except InvalidKeyError as e:
        raise NotFound(invalid_not_found_fmt.format(usage_key=usage_key_str)) from e

    block = load_block(usage_key, request.user, block_type_overrides=_block_type_overrides(request.GET))
    includes = request.GET.get("include", "").split(",")
    metadata_dict = get_block_metadata(block, includes=includes)
    if 'children' in metadata_dict:
        metadata_dict['children'] = [str(key) for key in metadata_dict['children']]
    if 'editable_children' in metadata_dict:
        metadata_dict['editable_children'] = [str(key) for key in metadata_dict['editable_children']]
    return Response(metadata_dict)


@api_view(['GET'])
@view_auth_classes(is_authenticated=False)
@permission_classes((permissions.AllowAny, ))  # Permissions are handled at a lower level, by the learning context
def render_block_view(request, usage_key_str, view_name):
    """
    Get the HTML, JS, and CSS needed to render the given XBlock.

    Accepts the following query parameters:
    * "lx_block_types": optional boolean; set to use the LabXchange XBlock classes to load the requested block.
      The block ID and OLX remain unchanged; they will use the original block type.
    """
    try:
        usage_key = UsageKey.from_string(usage_key_str)
    except InvalidKeyError as e:
        raise NotFound(invalid_not_found_fmt.format(usage_key=usage_key_str)) from e

    block = load_block(usage_key, request.user, block_type_overrides=_block_type_overrides(request.GET))
    fragment = _render_block_view(block, view_name, request.user)
    response_data = get_block_metadata(block)
    response_data.update(fragment.to_dict())
    return Response(response_data)


@api_view(['GET'])
@view_auth_classes(is_authenticated=False)
def get_handler_url(request, usage_key_str, handler_name):
    """
    Get an absolute URL which can be used (without any authentication) to call
    the given XBlock handler.

    The URL will expire but is guaranteed to be valid for a minimum of 2 days.

    The following query parameters will be appended to the returned handler_url:
    * "lx_block_types": optional boolean; set to use the LabXchange XBlock classes to load the requested block.
      The block ID and OLX remain unchanged; they will use the original block type.
    """
    try:
        usage_key = UsageKey.from_string(usage_key_str)
    except InvalidKeyError as e:
        raise NotFound(invalid_not_found_fmt.format(usage_key=usage_key_str)) from e

    handler_url = _get_handler_url(usage_key, handler_name, request.user, request.GET)
    return Response({"handler_url": handler_url})


# We cannot use DRF for this endpoint because its Request object is incompatible
# with the API expected by XBlock handlers.
# See https://github.com/openedx/edx-platform/pull/19253
# and https://github.com/openedx/XBlock/pull/383 for context.
@csrf_exempt
@xframe_options_exempt
def xblock_handler(request, user_id, secure_token, usage_key_str, handler_name, suffix=None):
    """
    Run an XBlock's handler and return the result

    This endpoint has a unique authentication scheme that involves a temporary
    auth token included in the URL (see below). As a result it can be exempt
    from CSRF, session auth, and JWT/OAuth.

    Accepts the following query parameters (in addition to those passed to the handler):

    * "lx_block_types": optional boolean; set to use the LabXchange XBlock classes to load the requested block.
      The block ID and OLX remain unchanged; they will use the original block type.
    """
    try:
        usage_key = UsageKey.from_string(usage_key_str)
    except InvalidKeyError as e:
        raise Http404 from e

    # To support sandboxed XBlocks, custom frontends, and other use cases, we
    # authenticate requests using a secure token in the URL. see
    # openedx.core.djangoapps.xblock.utils.get_secure_hash_for_xblock_handler
    # for details and rationale.
    if not validate_secure_token_for_xblock_handler(user_id, usage_key_str, secure_token):
        raise PermissionDenied("Invalid/expired auth token.")
    if request.user.is_authenticated:
        # The user authenticated twice, e.g. with session auth and the token.
        # This can happen if not running the XBlock in a sandboxed iframe.
        # Just make sure the session auth matches the token:
        if request.user.id != int(user_id):
            raise AuthenticationFailed("Authentication conflict.")
        user = request.user
    elif user_id.isdigit():
        # This is a normal (integer) user ID for a registered user.
        # This is the "normal" way this view gets used, with a sandboxed iframe.
        user = User.objects.get(pk=int(user_id))
    elif user_id.startswith("anon"):
        # This is a non-registered (anonymous) user:
        assert request.user.is_anonymous
        assert not hasattr(request.user, 'xblock_id_for_anonymous_user')
        user = request.user  # An AnonymousUser
        # Since this particular view usually gets called from a sandboxed iframe
        # we won't have access to the LMS session data for this user (the iframe
        # has a new, empty session). So we need to save the identifier for this
        # anonymous user (from the URL) on the user object, so that the runtime
        # can get it (instead of generating a new one and saving it into this
        # new empty session)
        # See djangoapps.xblock.utils.get_xblock_id_for_anonymous_user()
        user.xblock_id_for_anonymous_user = user_id
    else:
        raise AuthenticationFailed("Invalid user ID format.")

    request_webob = DjangoWebobRequest(request)  # Convert from django request to the webob format that XBlocks expect
    block = load_block(usage_key, user, block_type_overrides=_block_type_overrides(request.GET))
    # Run the handler, and save any resulting XBlock field value changes:
    response_webob = block.handle(handler_name, request_webob, suffix)
    response = webob_to_django_response(response_webob)
    return response


def cors_allow_xblock_handler(sender, request, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
    """
    Sandboxed XBlocks need to be able to call XBlock handlers via POST,
    from a different domain. See 'xblock_handler' method for details and how security is
    enforced.
    Per the corsheaders docs, a signal is the only way to achieve this for
    just a specific view/URL.
    """
    return request.path.startswith('/api/xblock/v2/xblocks/') and '/handler/' in request.path


check_request_enabled.connect(cors_allow_xblock_handler)
