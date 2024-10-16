"""
API Views for managing & syncing links between upstream & downstream content

Only [BETA] endpoints are implemented currently.
The [FULL] endpoints should be implemented for the Full Libraries Relaunch, or removed from this doc.

[FULL] List downstream blocks that can be synced, filterable by course or sync-readiness.
    GET /api/v2/contentstore/downstreams
    GET /api/v2/contentstore/downstreams?course_id=course-v1:A+B+C&ready_to_sync=true
      200: A paginated list of applicable & accessible downstream blocks.

[BETA] Inspect a single downstream block's link to upstream content.
    GET /api/v2/contentstore/downstreams/{usage_key_string}
      200: Upstream link details successfully fetched.
      404: Block not found, OR user lacks permission to read block.
      400: Block it not linked to upstream content.

[FULL] Sever a single downstream block's link to upstream content.
    DELETE /api/v2/contentstore/downstreams/{usage_key_string}
      204: Block successfully unlinked. No response body.
      403: User lacks permission to edit block.
      404: Block not found, OR user lacks permission to read block.
      400: Block it not linked to upstream content.

[BETA] Establish or modify a single downstream block's link to upstream content.
(This makes sense REST-wise, but I'm not sure we'll actually need it.)
    PUT /api/v2/contentstore/downstreams/{usage_key_string}
      REQUEST BODY: {
        "upstream_ref": str,  // reference to upstream block (eg, library block usage key)
        "sync": bool,  // whether to sync in upstream content (False by default)
      }
      200: Block's upstream link successfully edited (and synced, if requested).
      403: User lacks permission to edit block.
      404: Block not found, OR user lacks permission to read block.
      400: upstream_ref is malformed, missing, or inaccessible.
      400: Upstream block does not support syncing.

[BETA] Sync a downstream block with upstream content.
    POST /api/v2/contentstore/downstreams/{usage_key_string}/sync
      200: Block successfully synced with upstream content.
      403: User lacks permission to edit block.
      404: Block is not linked to upstream, OR block not found, OR user lacks permission to read block.
      400: Block it not linked to upstream content.
      400: Upstream is malformed, missing, or inaccessible.
      400: Upstream block does not support syncing.

[BETA] Decline an available sync for a downstream block.
    DELETE /api/v2/contentstore/downstreams/{usage_key_string}/sync
      204: Sync successfuly dismissed. No response body.
      403: User lacks permission to edit block.
      404: Block not found, OR user lacks permission to read block.
      400: Block it not linked to upstream content.

Schema for 200 responses, except where noted:
  {
      "upstream_ref": string?
      "version_synced": string?,
      "version_available": string?,
      "version_declined": string?,
      "error_message": string?,
      "ready_to_sync": Boolean
  }

Schema for 4XX responses:
  {
      "developer_message": string?
  }
"""
from django.contrib.auth.models import AbstractUser
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from xblock.core import XBlock

from cms.lib.xblock.upstream_sync import (
    UpstreamLink, sync_from_upstream, decline_sync, BadUpstream, BadDownstream, fetch_customizable_fields
)
from common.djangoapps.student.auth import has_studio_write_access, has_studio_read_access
from openedx.core.lib.api.view_utils import (
    DeveloperErrorViewMixin,
    view_auth_classes,
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


# TODO: Potential future view.
# @view_auth_classes(is_authenticated=True)
# class DownstreamListView(DeveloperErrorViewMixin, APIView):
#     """
#     List all blocks which are linked to upstream content, with optional filtering.
#     """
#     def get(self, request: Request) -> Response:
#         """
#         Handle the request.
#         """
#         course_key_string = request.GET['course_id']
#         syncable = request.GET['ready_to_sync']
#         ...


@view_auth_classes(is_authenticated=True)
class DownstreamView(DeveloperErrorViewMixin, APIView):
    """
    Inspect or manage an XBlock's link to upstream content.
    """
    def get(self, request: Request, usage_key_string: str) -> Response:
        """
        Inspect an XBlock's link to upstream content.
        """
        assert isinstance(request.user, AbstractUser)
        downstream = _load_accessible_downstream_block(request.user, usage_key_string, require_write_access=False)
        if link := UpstreamLink.try_get_for_block(downstream):
            return Response(link.to_json())
        raise ValidationError(detail=f"Block '{usage_key_string}' is not linked to an upstream")

    def put(self, request: Request, usage_key_string: str) -> Response:
        """
        Edit an XBlock's link to upstream content.
        """
        assert isinstance(request.user, AbstractUser)
        downstream = _load_accessible_downstream_block(request.user, usage_key_string, require_write_access=True)
        new_upstream_ref = request.data.get("upstream_ref")
        if not isinstance(new_upstream_ref, str):
            raise ValidationError(detail="missing value for upstream_ref in request body")
        downstream.upstream = new_upstream_ref
        try:
            if request.data.get("sync"):
                sync_from_upstream(downstream=downstream, user=request.user)
            else:
                fetch_customizable_fields(downstream=downstream, user=request.user)
        except (BadUpstream, BadDownstream) as exc:
            raise ValidationError(detail=str(exc)) from exc
        modulestore().update_item(downstream, request.user.id)
        link = UpstreamLink.get_for_block(downstream)
        assert link
        return Response(link.to_json())

    # def delete(self, request: Request, usage_key_string: str) -> Response:
    #     """
    #     Sever an XBlock's link to upstream content.
    #     """
    #


@view_auth_classes(is_authenticated=True)
class SyncFromUpstreamView(DeveloperErrorViewMixin, APIView):
    """
    Accept or decline an opportunity to sync a downstream block from its upstream content.
    """

    def post(self, request: Request, usage_key_string: str) -> Response:
        """
        Pull latest updates to the block at {usage_key_string} from its linked upstream content.
        """
        assert isinstance(request.user, AbstractUser)
        downstream = _load_accessible_downstream_block(request.user, usage_key_string, require_write_access=True)
        if not downstream.upstream:
            raise NotFound(detail=f"Block '{usage_key_string}' is not linked to a library block")
        old_version = downstream.upstream_version
        try:
            sync_from_upstream(downstream, request.user)
        except (BadUpstream, BadDownstream) as exc:
            raise ValidationError(detail=str(exc)) from exc
        modulestore().update_item(downstream, request.user.id)
        upstream_link = UpstreamLink.get_for_block(downstream)
        assert upstream_link
        return Response(upstream_link.to_json(), status=200)

    def delete(self, request: Request, usage_key_string: str) -> Response:
        """
        Handle the request.
        """
        assert isinstance(request.user, AbstractUser)
        downstream = _load_accessible_downstream_block(request.user, usage_key_string, require_write_access=True)
        try:
            decline_sync(downstream)
        except (BadUpstream, BadDownstream) as exc:
            raise ValidationError(str(exc)) from exc
        modulestore().update_item(downstream, request.user.id)
        return Response(status=204)


def _load_accessible_downstream_block(
    user: AbstractUser, usage_key_string: str, *, require_write_access: bool
) -> XBlock:
    """
    Given a logged in-user and a serialized usage key of an upstream-linked XBlock, load it from the ModuleStore,
    raising a DRF-friendly exception if anything goes wrong.

    Raises NotFound if usage key is malformed.
    Raises NotFound if user lacks read access.
    Raises PermissionDenied if `require_write_access` and user lacks write access.
    Raises NotFound if block does not exist.
    Raises ValidationError if block is not a downstream block.
    """
    not_found = NotFound(detail=f"Block not found or not accessible: {usage_key_string}")
    try:
        usage_key = UsageKey.from_string(usage_key_string)
    except InvalidKeyError as exc:
        raise ValidationError(detail=f"Malformed block usage key: {usage_key_string}") from exc
    if require_write_access:
        if not has_studio_write_access(user, usage_key.context_key):
            if has_studio_read_access(user, usage_key.context_key):
                # Raise a slightly more detailed 403 error for users with read access
                raise PermissionDenied(detail=f"User lacks permission to modify block: {usage_key_string}")
            raise not_found  # Users with no read access get an opaque 404 -- avoid leaking content info
    elif not has_studio_read_access(user, usage_key.context_key):
        raise not_found
    try:
        block = modulestore().get_item(usage_key)
    except ItemNotFoundError as exc:
        raise not_found from exc
    if not block.upstream:
        raise ValidationError(detail=f"Block '{usage_key_string}' is not linked to a library block")
    return block
