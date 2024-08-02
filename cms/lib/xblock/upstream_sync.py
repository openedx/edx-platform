"""
Synchronize content and settings from upstream blocks to their downstream usages.

At the time of writing, upstream blocks are assumed to come from content libraries,
and downstream blocks will generally belong to courses. However, the system is designed
to be mostly agnostic to exact type of upstream context and type of downstream context.
"""
import json
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.util.functional import cached_property
from django.utils.translation import gettext_lazy as _
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

def get_upstream_info(usage_key: UsageKey | str) -> UsageKey:
    """
    Raise an error if the provided key is not valid upstream reference.

    Currently, only Learning-Core-backed Content Library blocks are valid upstreams, although this may
    change in the future.

    Raises: InvalidKeyError, UnsupporteUpstreamKeyType
    """
    if isinstance(usage_key, str):
        usage_key = UsageKey.from_string(usage_key)
    if not isinstance(usage_key, LibraryUsageLocatorV2):
        raise UnsupportedUpstreamKeyType(
            "upstream key must be of type LibraryUsageLocatorV2; "
            f"provided key '{usage_key}' is of type '{type(usage_key)}'"
        )
    return usage_key


@dataclass(frozen=True)
class Upstream:

    @property
    def can_sync(self) -> bool:
        return False


@dataclass(frozen=True)
class NoUpstream(Upstream):
    pass


@dataclass(frozen=True)
class SomeUpstream(Upstream):
    current_version: int | None
    usage_key_string: str


@dataclass(frozen=True)
class BadUpstream(SomeUpstream):
    pass


@dataclass(frozen=True)
class BadUpstreamKeyString(BadUpstream):
    pass


@dataclass(frozen=True)
class BadUpstreamKeyType(BadUpstream):
    usage_key: UsageKey


@dataclass(frozen=True)
class BadUpstreamBlock(BadUpstream):
    usage_key: UsageKey
    error: str


@dataclass(frozen=True)
class GoodUpstream(Upstream):
    current_version: int | None
    usage_key: None


@dataclass(frozen=True)
class GoodUpstreamNoUpdates(GoodUpstream):
    pass


@dataclass(frozen=True)
class GoodUpstreamWithUpdates(GoodUpstream):
    latest_version: int
    sync_url: str

    @property
    def can_sync(self) -> bool
        return True


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
        default={}, enforce_type=True,
    )

    def save(self, *args, **kwargs):
        """
        Upon save, ensure that upstream_overriden tracks all upstream-provided fields which downstream has overridden.

        @@TODO use is_dirty instead of getattr for efficiency?
        """
        for field_name, value in self.upstream_settings.items():
            if field_name not in self.upstream_overridden:
                if value != getattr(self, field_name):
                    self.upstream_overridden.append(field_name)
        super().save()

    @XBlock.handler
    def sync_updates(self, request: Request, suffix=None) -> Response:
        """
        XBlock handler
        """
        if request.method != "POST":
            return Response(status_code=405)
        upstream_info = self.get_upstream_info()
        if upstream_info["sync_url"]:

            upstream_info = self.get_upstream_info()
        return upstream_info
            return Rseponse(
        if not self.upstream:
            return Response("no linked upstream", response=400)
        try:
            self.sync_from_upstream(user=request.user, apply_updates=True)
        except (InvalidKeyError, UnsupportedUpstreamKeyType):
            return Response(f"erene not a valid: {self.upstream}", status_code=400)
        except XBlockNotFoundError:
            return Response(f"could not load upstream block: {self.upstream}", status_code=400)
        self.save()
        return Response(status_code=200)

    @XBlock.handler
    def upstream_info(self, request: Request, _suffix=None) -> Response:
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
            self.upstream = None
            self.sync_with_upstream(apply_updates=False)
        elif request.method == "PUT":
            try:
                usage_key_string = json.loads(request.data["usage_key"])
            except json.JSONDecodeError:
                return Response("bad json", status_code=400)
            except KeyError:
                return Response("missing top-level key in json body: usage_key", status_code=400)
            try:
                validate_upstream_key(usage_key_string)
            except InvalidKeyError:
                return Response(f"not a valid usage key: {usage_key_string}", status_code=400)
            except UnsupportedUpstreamKeyType as exc:
                return Response(str(exc), status_code=400)
            self.upstream = usage_key_string
            try:
                self.sync_from_upstream(user=request.user, usage_key)
            except XBlockNotFoundError:
                return Response(f"could not load library block metadata: {usage_key}", status_code=400)
        elif request.method == "GET":
            pass
        else
            return Response(status_code=405)
        upstream_info = self.get_upstream_info()
        if upstream_info:
            return Response(json.dumps(upstream_info, indent=4))
        else:
            return Response(status_code=204)

    def get_upstream_info(self) -> Upstream:
        """
        """
        if not self.upstream:
            return NoUpstream()
        latest: int | None = None
        error: str | None = None
        try:
            latest = self._lib_block.version_num
        except InvalidKeyError:
            error = _("Reference to linked library item is malformed: {}").format(block.upstream)
            latest = None
        except XBlockNotFoundError:
            error = _("Linked library item was not found in the system: {}").format(block.upstream)
            latest = None
        return UpstreamInfo(
            usage_key=self.upstream,
            current_version=self.upstream_version,
            latest_version=latest,
            sync_url=self.runtime.handler_url(self, 'sync_updates')
            error=error,
        )

    def sync_from_upstream(self, *, user: User, apply_updates: bool):
        """
        @@TODO docstring

        Raises: InvalidKeyError, UnsupportedUpstreamKeyType, XBlockNotFoundError
        """
        if not self.upstream:
            self.upstream_settings = {}
            self.upstream_overridden = []
            self.upstream_version = None
        upstream_key = usage_key = validate_upstream_key(self.upstream)
        self.upstream_settings = {}
        try:
            upstream_block = xblock_api.load_block(upstream_key, user)
        except NotFound as exc:
            raise XBlockNotFoundError(
                f"failed to load upstream ({self.upstream)} for block ({self.usage_key)} for user id={user.id}"
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
        self.upstream_version = self._lib_block.version_num
        self.save()
        # @@TODO why isn't self.save() sufficient? do we really need to invoke modulestore here?
        from xmodule.modulestore.django import modulestore  # pylint: disable=wrong-import-order
        modulestore().update_item(self, user.id)

    @cached_property
    def _lib_block(self) -> LibraryXBlockMetadata | None:
        """
        Internal cache of the upstream XBlock metadata, or None if there is none.

        We assume, for now, that upstreams are always Learning-Core-backed Content Library blocks.
        That is an INTERNAL ASSUMPTION that may change at some point; hence, this is a private
        property; callers should use the public API methods which don't assume that the upstream is
        a from a content library.

        Raises: InvalidKeyError, XBlockNotFoundError
        """
        if not self.upstream:
            return None
        upstream_key = validate_upstream_key(self.upstream)
        return get_library_block(upstream_key)
