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

  /api/contentstore/v2/upstream/{usage_key_string}/downstream-links

    GET: List all downstream blocks linked to a library block.
        200: A list of downstream usage_keys linked to the library block.

  /api/contentstore/v2/downstreams
  /api/contentstore/v2/downstreams?course_id=course-v1:A+B+C&ready_to_sync=true
      GET: List downstream blocks that can be synced, filterable by course or sync-readiness.
        200: A paginated list of applicable & accessible downstream blocks. Entries are ComponentLinks.

  /api/contentstore/v2/downstreams/<course_key>/summary
      GET: List summary of links by course key
        200: A list of summary of links by course key
        Example:
        [
            {
                "upstream_context_title": "CS problems 3",
                "upstream_context_key": "lib:OpenedX:CSPROB3",
                "ready_to_sync_count": 11,
                "total_count": 14
            },
            {
                "upstream_context_title": "CS problems 2",
                "upstream_context_key": "lib:OpenedX:CSPROB2",
                "ready_to_sync_count": 15,
                "total_count": 24
            },
        ]

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

from attrs import asdict as attrs_asdict
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from edx_rest_framework_extensions.paginators import DefaultPagination
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryUsageLocatorV2, LibraryContainerLocator
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.fields import BooleanField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from xblock.core import XBlock

from cms.djangoapps.contentstore.models import ComponentLink
from cms.djangoapps.contentstore.rest_api.v2.serializers import (
    ComponentLinksSerializer,
    PublishableEntityLinksSummarySerializer,
)
from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import sync_library_content
from cms.lib.xblock.upstream_sync import (
    BadDownstream,
    BadUpstream,
    NoUpstream,
    UpstreamLink,
    UpstreamLinkException,
    decline_sync,
    sever_upstream_link,
)
from cms.lib.xblock.upstream_sync_block import fetch_customizable_fields_from_block
from cms.lib.xblock.upstream_sync_container import fetch_customizable_fields_from_container
from common.djangoapps.student.auth import has_studio_read_access, has_studio_write_access
from openedx.core.lib.api.view_utils import (
    DeveloperErrorViewMixin,
    view_auth_classes,
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.video_block.transcripts_utils import clear_transcripts

logger = logging.getLogger(__name__)


class _AuthenticatedRequest(Request):
    """
    Alias for the `Request` class which tells mypy to assume that `.user` is not an AnonymousUser.

    Using this does NOT ensure the request is actually authenticated--
    you will some other way to ensure that, such as `@view_auth_classes(is_authenticated=True)`.
    """
    user: User


class DownstreamListPaginator(DefaultPagination):
    """Custom paginator for downstream entity links"""
    page_size = 100
    max_page_size = 1000

    def paginate_queryset(self, queryset, request, view=None):
        if 'no_page' in request.query_params:
            return queryset

        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data, *args, **kwargs):
        if 'no_page' in args[0].query_params:
            return Response(data)
        response = super().get_paginated_response(data)
        # replace next and previous links by next and previous page number
        response.data.update({
            'next_page_num': self.page.next_page_number() if self.page.has_next() else None,
            'previous_page_num': self.page.previous_page_number() if self.page.has_previous() else None,
        })
        return response


@view_auth_classes()
class DownstreamListView(DeveloperErrorViewMixin, APIView):
    """
    List all blocks which are linked to an upstream context, with optional filtering.
    """

    def get(self, request: _AuthenticatedRequest):
        """
        Fetches publishable entity links for given course key
        """
        course_key_string = request.GET.get('course_id')
        ready_to_sync = request.GET.get('ready_to_sync')
        upstream_usage_key = request.GET.get('upstream_usage_key')
        link_filter: dict[str, CourseKey | UsageKey | bool] = {}
        paginator = DownstreamListPaginator()
        if course_key_string:
            try:
                link_filter["downstream_context_key"] = CourseKey.from_string(course_key_string)
            except InvalidKeyError as exc:
                raise ValidationError(detail=f"Malformed course key: {course_key_string}") from exc
        if ready_to_sync is not None:
            link_filter["ready_to_sync"] = BooleanField().to_internal_value(ready_to_sync)
        if upstream_usage_key:
            try:
                link_filter["upstream_usage_key"] = UsageKey.from_string(upstream_usage_key)
            except InvalidKeyError as exc:
                raise ValidationError(detail=f"Malformed usage key: {upstream_usage_key}") from exc
        links = ComponentLink.filter_links(**link_filter)
        paginated_links = paginator.paginate_queryset(links, self.request, view=self)
        serializer = ComponentLinksSerializer(paginated_links, many=True)
        return paginator.get_paginated_response(serializer.data, self.request)


@view_auth_classes()
class DownstreamSummaryView(DeveloperErrorViewMixin, APIView):
    """
    Serves course->library publishable entity links summary
    """
    def get(self, request: _AuthenticatedRequest, course_key_string: str):
        """
        Fetches publishable entity links summary for given course key
        Example:
        [
            {
                "upstream_context_title": "CS problems 3",
                "upstream_context_key": "lib:OpenedX:CSPROB3",
                "ready_to_sync_count": 11,
                "total_count": 14
                "last_published_at": "2025-05-02T20:20:44.989042Z"
            },
            {
                "upstream_context_title": "CS problems 2",
                "upstream_context_key": "lib:OpenedX:CSPROB2",
                "ready_to_sync_count": 15,
                "total_count": 24,
                "last_published_at": "2025-05-03T21:20:44.989042Z"
            },
        ]
        """
        try:
            course_key = CourseKey.from_string(course_key_string)
        except InvalidKeyError as exc:
            raise ValidationError(detail=f"Malformed course key: {course_key_string}") from exc
        links = ComponentLink.summarize_by_downstream_context(downstream_context_key=course_key)
        serializer = PublishableEntityLinksSummarySerializer(links, many=True)
        return Response(serializer.data)


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
        sync_param = request.data.get("sync", "false")
        if isinstance(sync_param, str):
            sync_param = sync_param.lower()
        if sync_param not in ["true", "false", True, False]:
            raise ValidationError({"sync": "must be 'true' or 'false'"})
        try:
            if sync_param == "true" or sync_param is True:
                sync_library_content(
                    downstream=downstream,
                    request=request,
                    store=modulestore()
                )
            else:
                # Even if we're not syncing (i.e., updating the downstream's values with the upstream's), we still need
                # to fetch the upstream's customizable values and store them as hidden fields on the downstream. This
                # ensures that downstream authors can restore defaults based on the upstream.
                link = UpstreamLink.get_for_block(downstream)
                if isinstance(link.upstream_key, LibraryUsageLocatorV2):
                    fetch_customizable_fields_from_block(downstream=downstream, user=request.user)
                else:
                    assert isinstance(link.upstream_key, LibraryContainerLocator)
                    fetch_customizable_fields_from_container(downstream=downstream)
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
        except NoUpstream:
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
            if downstream.usage_key.block_type == "video":
                # Delete all transcripts so we can copy new ones from upstream
                clear_transcripts(downstream)
            static_file_notices = sync_library_content(
                downstream=downstream,
                request=request,
                store=modulestore()
            )
        except UpstreamLinkException as exc:
            logger.exception(
                "Could not sync from upstream '%s' to downstream '%s'",
                downstream.upstream,
                usage_key_string,
            )
            raise ValidationError(detail=str(exc)) from exc
        # Note: We call `get_for_block` (rather than `try_get_for_block`) because if anything is wrong with the
        #       upstream at this point, then that is completely unexpected, so it's appropriate to let the 500 happen.
        response = UpstreamLink.get_for_block(downstream).to_json()
        response["static_file_notices"] = attrs_asdict(static_file_notices)
        return Response(response)

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
