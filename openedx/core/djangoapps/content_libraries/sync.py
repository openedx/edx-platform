"""
Synchronize content and settings from upstream blocks (in content libraries) to their
downstream usages (in courses, etc.)

At the time of writing, upstream blocks are assumed to come from content libraries.
However, the XBlock fields are designed to be agnostic to their upstream's source context,
so this assumption could be relaxed in the future if there is a need for upstreams from
other kinds of learning contexts.
"""
import json

from django.contrib.auth import get_user_model
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryUsageLocatorV2
from xblock.fields import Scope, String, Integer, List, Dict
from xblock.core import XBlockMixin, XBlock
from webob import Request, Response

from openedx.core.djangoapps.content_libraries.api import (
    get_library_block,
    LibraryXBlockMetadata,
    ContentLibraryBlockNotFound,
)
from openedx.core.djangoapps.xblock.api import load_block, NotFound as XBlockNotFound


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

    def assign_upstream(self, upstream_key: LibraryUsageLocatorV2, user_id: int) -> None:
        """
        Assign an upstream to this block and fetch upstream settings.

        Does not save block; caller must do so.

        @@TODO params
        """
        old_upstream = self.upstream
        self.upstream = str(upstream_key)
        try:
            self._sync_with_upstream(user_id=user_id, apply_updates=False)
        except BadUpstream:
            self.upstream = old_upstream
            raise
        self.save()

    @XBlock.handler
    def upstream_link(self, request: Request, _suffix=None) -> Response:
        """
        @@TODO docstring
        @@TODO more data?
        """
        # @@TODO: There *has* to be a way to load a learning core block without invoking the user service...
        user_id = self.runtime.service(self, "user")._django_user.id
        if request.method == "GET":
            try:
                upstream_block, upstream_meta = self._load_upstream(user_id)
            except BadUpstream as exc:
                return Response(str(exc), status_code=400)
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
        if request.method == "PUT":
            # @@TODO better validation
            try:
                self.assign_upstream(UsageKey.from_string(json.loads(request.data["usage_key"])), user_id)
            except BadUpstream as exc:
                return Response(str(exc), status_code=400)
            return Response(status_code=204)  # @@TODO what to returN?
        return Response(status_code=405)

    @XBlock.handler
    def update_from_upstream(self, request: Request, suffix=None) -> Response:
        """
        @@TODO docstring
        """
        if request.method != "POST":
            return Response(status_code=405)
        try:
            user_id = request.user.id if request and request.user else 0
            self._sync_with_upstream(user_id=user_id, apply_updates=True)
        except BadUpstream as exc:
            return Response(str(exc), status_code=400)
        self.save()
        return Response(status_code=204)

    def _sync_with_upstream(self, *, user_id: int, apply_updates: bool) -> None:
        """
        @@TODO docstring

        Does not save block; caller must do so.

        Can raise NoUpstream or BadUpstream.
        """
        upstream, upstream_meta = self._load_upstream(user_id)
        self.upstream_settings = {}
        self.upstream_version = upstream_meta.version_num
        for field_name, field in upstream.fields.items():
            if field.scope not in [Scope.settings, Scope.content]:
                continue
            value = getattr(upstream, field_name)
            if field.scope == Scope.settings:
                self.upstream_settings[field_name] = value
                if field_name in self.upstream_overridden:
                    continue
            if not apply_updates:
                continue
            setattr(self, field_name, value)

    def _load_upstream(self, user_id: int) -> tuple[XBlock, LibraryXBlockMetadata]:
        """
        This this block's upstream from a content library.

        Raises BadUpstream if the upstream block could not be loaded for any reason.
        """
        cannot_load = f"Cannot load updates for component at '{self.usage_key}'"
        if not self.upstream:
            raise BadUpstream(f"{cannot_load}: no linked content library item")
        try:
            print(self.upstream)
            upstream_key = LibraryUsageLocatorV2.from_string(self.upstream)
        except InvalidKeyError as exc:
            raise BadUpstream(
                f"{cannot_load}: invalid content library item reference '{self.upstream}'"
            ) from exc
        try:
            upstream_meta = get_library_block(upstream_key)
        except ContentLibraryBlockNotFound as exc:
            raise BadUpstream(
                f"{cannot_load}: linked item '{upstream_key}' does not belong to a content library"
            ) from exc
        try:
            upstream = load_block(upstream_key, get_user_model().objects.get(id=user_id))
        except XBlockNotFound as exc:
            raise BadUpstream(
                f"{cannot_load}: failed to load linked content library item at '{upstream_key}'. "
                "Either the item was deleted, or you lack permission to view its contents."
            ) from exc
        return upstream, upstream_meta


class BadUpstream(Exception):
    """
    Base exception for any content-level problems we can hit while loading a block's upstream.

    Should not represent unexpected internal server errors.
    May appear in API responses, so they should be somewhat user friendly and avoid sensitive info.
    """


def is_valid_upstream(usage_key: UsageKey) -> bool:
    """
    @@TODO docstring
    """
    return isinstance(usage_key, LibraryUsageLocatorV2)
