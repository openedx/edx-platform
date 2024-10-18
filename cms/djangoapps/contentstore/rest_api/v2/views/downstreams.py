"""
API Views for managing & syncing links between upstream & downstream content

API paths (We will move these into proper api_doc_tools annotations soon
https://github.com/openedx/edx-platform/issues/35653):

  /api/contentstore/v2/downstreams/{usage_key_string}

    GET: Inspect a single downstream block's link to upstream content.
      200: Upstream link details successfully fetched. Returns UpstreamLink (may contain an error_message).
      404: Downstream block not found or user lacks permission to edit it.

    DELETE: Sever a single downstream block's link to upstream content.
      204: Block successfully unlinked (or it wasn't linked in the first place). No response body.
      404: Downstream block not found or user lacks permission to edit it.

    PUT: Establish or modify a single downstream block's link to upstream content. An authoring client could use this
         endpoint to add library content in a two-step process, specifically: (1) add a blank block to a course, then
         (2) link it to a content library with ?sync=True.
      REQUEST BODY: {
        "upstream_ref": str,  // reference to upstream block (eg, library block usage key)
        "sync": bool,  // whether to sync in upstream content (False by default)
      }
      200: Downstream block's upstream link successfully edited (and synced, if requested). Returns UpstreamLink.
      400: upstream_ref is malformed, missing, or inaccessible.
      400: Content at upstream_ref does not support syncing.
      404: Downstream block not found or user lacks permission to edit it.

  /api/contentstore/v2/downstreams/{usage_key_string}/sync

    POST: Sync a downstream block with upstream content.
      200: Downstream block successfully synced with upstream content.
      400: Downstream block is not linked to upstream content.
      400: Upstream is malformed, missing, or inaccessible.
      400: Upstream block does not support syncing.
      404: Downstream block not found or user lacks permission to edit it.

    DELETE: Decline an available sync for a downstream block.
      204: Sync successfuly dismissed. No response body.
      400: Downstream block is not linked to upstream content.
      404: Downstream block not found or user lacks permission to edit it.

  # NOT YET IMPLEMENTED -- Will be needed for full Libraries Relaunch in ~Teak.
  /api/contentstore/v2/downstreams
  /api/contentstore/v2/downstreams?course_id=course-v1:A+B+C&ready_to_sync=true
      GET: List downstream blocks that can be synced, filterable by course or sync-readiness.
        200: A paginated list of applicable & accessible downstream blocks. Entries are UpstreamLinks.

UpstreamLink response schema:
  {
    "upstream_ref": string?
    "version_synced": string?,
    "version_available": string?,
    "version_declined": string?,
    "error_message": string?,
    "ready_to_sync": Boolean
  }
"""
import logging

from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from xblock.core import XBlock

from cms.lib.xblock.upstream_sync import (
    UpstreamLink, UpstreamLinkException, NoUpstream, BadUpstream, BadDownstream,
    fetch_customizable_fields, sync_from_upstream, decline_sync, sever_upstream_link
)
from common.djangoapps.student.auth import has_studio_write_access, has_studio_read_access
from openedx.core.lib.api.view_utils import (
    DeveloperErrorViewMixin,
    view_auth_classes,
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


logger = logging.getLogger(__name__)


class _AuthenticatedRequest(Request):
    """
    Alias for the `Request` class which tells mypy to assume that `.user` is not an AnonymousUser.

    Using this does NOT ensure the request is actually authenticated--
    you will some other way to ensure that, such as `@view_auth_classes(is_authenticated=True)`.
    """
    user: User


# TODO: Potential future view.
# @view_auth_classes(is_authenticated=True)
# class DownstreamListView(DeveloperErrorViewMixin, APIView):
#     """
#     List all blocks which are linked to upstream content, with optional filtering.
#     """
#     def get(self, request: _AuthenticatedRequest) -> Response:
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
    def get(self, request: _AuthenticatedRequest, usage_key_string: str) -> Response:
        """
        Inspect an XBlock's link to upstream content.
        """
        downstream = _load_accessible_block(request.user, usage_key_string, require_write_access=False)
        return Response(UpstreamLink.try_get_for_block(downstream).to_json())

    def put(self, request: _AuthenticatedRequest, usage_key_string: str) -> Response:
        """
        Edit an XBlock's link to upstream content.
        """
        downstream = _load_accessible_block(request.user, usage_key_string, require_write_access=True)
        new_upstream_ref = request.data.get("upstream_ref")

        # Set `downstream.upstream` so that we can try to sync and/or fetch.
        # Note that, if this fails and we raise a 4XX, then we will not call modulstore().update_item,
        # thus preserving the former value of `downstream.upstream`.
        downstream.upstream = new_upstream_ref
        sync_param = request.data.get("sync", "false").lower()
        if sync_param not in ["true", "false"]:
            raise ValidationError({"sync": "must be 'true' or 'false'"})
        try:
            if sync_param == "true":
                sync_from_upstream(downstream=downstream, user=request.user)
            else:
                # Even if we're not syncing (i.e., updating the downstream's values with the upstream's), we still need
                # to fetch the upstream's customizable values and store them as hidden fields on the downstream. This
                # ensures that downstream authors can restore defaults based on the upstream.
                fetch_customizable_fields(downstream=downstream, user=request.user)
        except BadDownstream as exc:
            logger.exception(
                "'%s' is an invalid downstream; refusing to set its upstream to '%s'",
                usage_key_string,
                new_upstream_ref,
            )
            raise ValidationError(str(exc)) from exc
        except BadUpstream as exc:
            logger.exception(
                "'%s' is an invalid upstream reference; refusing to set it as upstream of '%s'",
                new_upstream_ref,
                usage_key_string,
            )
            raise ValidationError({"upstream_ref": str(exc)}) from exc
        except NoUpstream as exc:
            raise ValidationError({"upstream_ref": "value missing"}) from exc
        modulestore().update_item(downstream, request.user.id)
        # Note: We call `get_for_block` (rather than `try_get_for_block`) because if anything is wrong with the
        #       upstream at this point, then that is completely unexpected, so it's appropriate to let the 500 happen.
        return Response(UpstreamLink.get_for_block(downstream).to_json())

    def delete(self, request: _AuthenticatedRequest, usage_key_string: str) -> Response:
        """
        Sever an XBlock's link to upstream content.
        """
        downstream = _load_accessible_block(request.user, usage_key_string, require_write_access=True)
        try:
            sever_upstream_link(downstream)
        except NoUpstream as exc:
            logger.exception(
                "Tried to DELETE upstream link of '%s', but it wasn't linked to anything in the first place. "
                "Will do nothing. ",
                usage_key_string,
            )
        else:
            modulestore().update_item(downstream, request.user.id)
        return Response(status=204)


@view_auth_classes(is_authenticated=True)
class SyncFromUpstreamView(DeveloperErrorViewMixin, APIView):
    """
    Accept or decline an opportunity to sync a downstream block from its upstream content.
    """

    def post(self, request: _AuthenticatedRequest, usage_key_string: str) -> Response:
        """
        Pull latest updates to the block at {usage_key_string} from its linked upstream content.
        """
        downstream = _load_accessible_block(request.user, usage_key_string, require_write_access=True)
        try:
            sync_from_upstream(downstream, request.user)
        except UpstreamLinkException as exc:
            logger.exception(
                "Could not sync from upstream '%s' to downstream '%s'",
                downstream.upstream,
                usage_key_string,
            )
            raise ValidationError(detail=str(exc)) from exc
        modulestore().update_item(downstream, request.user.id)
        # Note: We call `get_for_block` (rather than `try_get_for_block`) because if anything is wrong with the
        #       upstream at this point, then that is completely unexpected, so it's appropriate to let the 500 happen.
        return Response(UpstreamLink.get_for_block(downstream).to_json())

    def delete(self, request: _AuthenticatedRequest, usage_key_string: str) -> Response:
        """
        Decline the latest updates to the block at {usage_key_string}.
        """
        downstream = _load_accessible_block(request.user, usage_key_string, require_write_access=True)
        try:
            decline_sync(downstream)
        except (NoUpstream, BadUpstream, BadDownstream) as exc:
            # This is somewhat unexpected. If the upstream link is missing or invalid, then the downstream author
            # shouldn't have been prompted to accept/decline a sync in the first place. Of course, they could have just
            # hit the HTTP API anyway, or they could be viewing a Studio page which hasn't been refreshed in a while.
            # So, it's a 400, not a 500.
            logger.exception(
                "Tried to decline a sync to downstream '%s', but the upstream link '%s' is invalid.",
                usage_key_string,
                downstream.upstream,
            )
            raise ValidationError(str(exc)) from exc
        modulestore().update_item(downstream, request.user.id)
        return Response(status=204)


def _load_accessible_block(user: User, usage_key_string: str, *, require_write_access: bool) -> XBlock:
    """
    Given a logged in-user and a serialized usage key of an upstream-linked XBlock, load it from the ModuleStore,
    raising a DRF-friendly exception if anything goes wrong.

    Raises NotFound if usage key is malformed, if the user lacks access, or if the block doesn't exist.
    """
    not_found = NotFound(detail=f"Block not found or not accessible: {usage_key_string}")
    try:
        usage_key = UsageKey.from_string(usage_key_string)
    except InvalidKeyError as exc:
        raise ValidationError(detail=f"Malformed block usage key: {usage_key_string}") from exc
    if require_write_access and not has_studio_write_access(user, usage_key.context_key):
        raise not_found
    if not has_studio_read_access(user, usage_key.context_key):
        raise not_found
    try:
        block = modulestore().get_item(usage_key)
    except ItemNotFoundError as exc:
        raise not_found from exc
    return block
