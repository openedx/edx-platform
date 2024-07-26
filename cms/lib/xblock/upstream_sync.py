"""
Synchronize content and settings from upstream blocks to their downstream usages.

At the time of writing, upstream blocks are assumed to come from content libraries,
and downstream blocks will generally belong to courses. However, the system is designed
to be mostly agnostic to exact type of upstream context and type of downstream context.
"""
import json

from django.contrib.auth import get_user_model
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryUsageLocatorV2
from rest_framework.exceptions import NotFound
from xblock.exceptions import XBlockNotFoundError
from xblock.fields import Scope, String, Integer, List, Dict
from xblock.core import XBlockMixin, XBlock
from webob import Request, Response

import openedx.core.djangoapps.xblock.api as xblock_api
from openedx.core.djangoapps.content_libraries.api import (
    get_library_block,
    LibraryXBlockMetadata,
)


class UpstreamSyncMixin(XBlockMixin):
    """
    @@TODO docstring
    """

    upstream = String(
        scope=Scope.settings,
        help=(
            "The usage key of a block (generally within a Content Library) which serves as a source of upstream "
            "updates for this block, or None if there is no such upstream. Please note: It is valid for upstream_block "
            "to hold a usage key for a block that does not exist (or does not *yet* exist) on this instance, "
            "particularly if this block was imported from a different instance."
        ),
        hidden=True,
        default=None,
        enforce_type=True,
    )
    upstream_version = Integer(
        scope=Scope.settings,
        help=(
            "The upstream_block's version number, at the time this block was created from it. "
            "If this version is older than the upstream_block's latest version, then CMS will "
            "allow this block to fetch updated content from upstream_block."
        ),
        hidden=True,
        default=None,
        enforce_type=True,
    )
    upstream_overridden = List(
        scope=Scope.settings,
        help=(
            "@@TODO helptext"
        ),
        hidden=True,
        default=[],
        enforce_type=True,
    )
    upstream_settings = Dict(
        scope=Scope.settings,
        help=(
            "@@TODO helptext"
        ),
        hidden=True,
        default={},
        enforce_type=True,
    )

    def save(self, *args, **kwargs):
        """
        @@TODO docstring
        @@TODO use is_dirty instead of getattr for efficiency?
        """
        for field_name, value in self.upstream_settings.items():
            if field_name not in self.upstream_overridden:
                if value != getattr(self, field_name):
                    self.upstream_overridden.append(field_name)
        super().save()

    def assign_upstream(self, upstream_key: LibraryUsageLocatorV2 | None) -> LibraryXBlockMetadata | None:
        """
        Assign an upstream to this block and fetch upstream settings.

        Raises: XBlockNotFoundError
        """
        old_upstream = self.upstream
        self.upstream = str(upstream_key)
        try:
            return self._sync_with_upstream(apply=False)
        except (InvalidKeyError, XBlockNotFoundError):
            self.upstream = old_upstream
            raise

    @XBlock.handler
    def upstream_link(self, request: Request, _suffix=None) -> Response:
        """
        @@TODO docstring

        GET: Retrieve upstream link
        PUT: Set upstream link
        DELETE: Remove upstream link

        200: Success, with JSON data on upstream link
        204: Success, no upstream link
        400: Bad request data
        401: Unauthenticated
        405: Bad method
        """
        if request.method == "DELETE":
            self.assign_upstream(None)
            return Response(status_code=204)
        if request.method in ["PUT", "GET"]:
            if request.method == "PUT":
                try:
                    usage_key_string = json.loads(request.data["usage_key"])
                except json.JSONDecodeError:
                    return Response("bad json", status_code=400)
                except KeyError:
                    return Response("missing top-level key in json body: usage_key", status_code=400)
                try:
                    usage_key = LibraryUsageLocatorV2.from_string(usage_key_string)
                except InvalidKeyError:
                    return Response(f"not a valid library block usage key: {usage_key_string}", status_code=400)
                try:
                    upstream_meta = self.assign_upstream(usage_key)  # type: ignore[assignment]
                except XBlockNotFoundError:
                    return Response(f"could not load library block metadata: {usage_key}", status_code=400)
            if request.method == "GET":
                try:
                    upstream_meta = self.get_upstream_meta()
                except InvalidKeyError:
                    return Response(f"upstream is not a valid usage key: {self.upstream}", status_code=400)
                except XBlockNotFoundError:
                    return Response(f"could not load upstream block metadata: {self.upstream}", status_code=400)
                if not upstream_meta:
                    return Response(status_code=204)
            return Response(
                json.dumps(
                    {
                        "usage_key": self.upstream,
                        "version_current": self.upstream_version,
                        "version_latest": upstream_meta.version_num if upstream_meta else None,
                    },
                    indent=4,
                ),
            )
        return Response(status_code=405)

    @XBlock.handler
    def upgrade_and_sync(self, request: Request, suffix=None) -> Response:
        """
        @@TODO docstring
        """
        if request.method != "POST":
            return Response(status_code=405)
        if not self.upstream:
            return Response("no linked upstream", response=400)
        try:
            self._sync_with_upstream(apply=True)
        except InvalidKeyError:
            return Response(f"upstream is not a valid usage key: {self.upstream}", status_code=400)
        except XBlockNotFoundError:
            return Response(f"could not load upstream block: {self.upstream}", status_code=400)
        self.save()
        return Response(status_code=200)

    def _sync_with_upstream(self, *, apply: bool) -> LibraryXBlockMetadata | None:
        """
        @@TODO docstring

        Raises: InvalidKeyError, XBlockNotFoundError
        """
        upstream_meta = self.get_upstream_meta()
        if not upstream_meta:
            self.upstream_overridden = []
            self.upstream_version = None
            return None
        self.upstream_settings = {}
        # @@TODO: do we need user_id to get the block? if so, is there a better way to get it?
        user_id = self.runtime.service(self, "user")._django_user.id  # pylint: disable=protected-access
        try:
            upstream_block = xblock_api.load_block(upstream_meta.usage_key, get_user_model().objects.get(id=user_id))
        except NotFound as exc:
            raise XBlockNotFoundError(
                f"failed to load upstream block for user id={user_id}: {self.upstream}"
            ) from exc
        for field_name, field in upstream_block.fields.items():
            if field.scope not in [Scope.settings, Scope.content]:
                continue
            value = getattr(upstream_block, field_name)
            if field.scope == Scope.settings:
                self.upstream_settings[field_name] = value
                if field_name in self.upstream_overridden:
                    continue
            if not apply:
                continue
            setattr(self, field_name, value)
        self.upstream_version = upstream_meta.version_num
        self.save()
        # @@TODO why isn't self.save() sufficient? do we really need to invoke modulestore here?
        from xmodule.modulestore.django import modulestore  # pylint: disable=wrong-import-order
        modulestore().update_item(self, user_id)
        return upstream_meta

    def get_upstream_meta(self) -> LibraryXBlockMetadata | None:
        """
        Get metadata about the upstream XBlock, or None if there is none.

        Currently, this always returns LibraryXBlockMetadata; in the future, it could
        return other metadata, so callers should check the return type.

        Raises: InvalidKeyError, XBlockNotFoundError
        """
        if not self.upstream:
            return None
        upstream_key = LibraryUsageLocatorV2.from_string(self.upstream)
        return get_library_block(upstream_key)


def is_valid_upstream(usage_key: UsageKey) -> bool:
    """
    Does this key refer to a block that can be used as an upstream?

    Currently, only Learning-Core-backed Content Library blocks are valid upstreams.
    """
    return isinstance(usage_key, LibraryUsageLocatorV2)
