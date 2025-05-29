"""
Methods related to syncing a downstream XBlock with an upstream XBlock.

See upstream_sync.py for general upstream sync code that applies even when the
upstream is a container, not an XBlock.
"""
from __future__ import annotations

import typing as t

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import NotFound
from opaque_keys.edx.locator import LibraryUsageLocatorV2
from xblock.fields import Scope
from xblock.core import XBlock

from .upstream_sync import UpstreamLink, BadUpstream

if t.TYPE_CHECKING:
    from django.contrib.auth.models import User  # pylint: disable=imported-auth-user


def sync_from_upstream_block(downstream: XBlock, user: User) -> XBlock:
    """
    Update `downstream` with content+settings from the latest available version of its linked upstream content.

    Preserves overrides to customizable fields; overwrites overrides to other fields.
    Does not save `downstream` to the store. That is left up to the caller.

    ⭐️ Does not save changes to modulestore nor handle static assets. The caller
    will have to take care of that.

    If `downstream` lacks a valid+supported upstream link, this raises an UpstreamLinkException.
    """
    link = UpstreamLink.get_for_block(downstream)  # can raise UpstreamLinkException
    if not isinstance(link.upstream_key, LibraryUsageLocatorV2):
        raise TypeError("sync_from_upstream_block() only supports XBlock upstreams, not containers")
    # Upstream is a library block:
    upstream = _load_upstream_block(downstream, user)
    _update_customizable_fields(upstream=upstream, downstream=downstream, only_fetch=False)
    _update_non_customizable_fields(upstream=upstream, downstream=downstream)
    _update_tags(upstream=upstream, downstream=downstream)
    downstream.upstream_version = link.version_available
    return upstream


def fetch_customizable_fields_from_block(*, downstream: XBlock, user: User, upstream: XBlock | None = None) -> None:
    """
    Fetch upstream-defined value of customizable fields and save them on the downstream.

    If `upstream` is provided, use that block as the upstream.
    Otherwise, load the block specified by  `downstream.upstream`, which may raise an UpstreamLinkException.
    """
    if not upstream:
        upstream = _load_upstream_block(downstream, user)
    _update_customizable_fields(upstream=upstream, downstream=downstream, only_fetch=True)


def _load_upstream_block(downstream: XBlock, user: User) -> XBlock:
    """
    Load the upstream metadata and content for a downstream block.

    Assumes that the upstream content is an XBlock in an LC-backed content libraries. This assumption may need to be
    relaxed in the future (see module docstring).

    If `downstream` lacks a valid+supported upstream link, this raises an UpstreamLinkException.
    """
    # We import load_block here b/c UpstreamSyncMixin is used by cms/envs, which loads before the djangoapps are ready.
    from openedx.core.djangoapps.xblock.api import load_block, CheckPerm, LatestVersion  # pylint: disable=wrong-import-order
    try:
        lib_block: XBlock = load_block(
            LibraryUsageLocatorV2.from_string(downstream.upstream),
            user,
            check_permission=CheckPerm.CAN_READ_AS_AUTHOR,
            version=LatestVersion.PUBLISHED,
        )
    except (NotFound, PermissionDenied) as exc:
        raise BadUpstream(_("Linked library item could not be loaded: {}").format(downstream.upstream)) from exc
    return lib_block


def _update_customizable_fields(*, upstream: XBlock, downstream: XBlock, only_fetch: bool) -> None:
    """
    For each customizable field:
    * Save the upstream value to a hidden field on the downstream ("FETCH").
    * If `not only_fetch`, and if the field *isn't* customized on the downstream, then:
      * Update it the downstream field's value from the upstream field ("SYNC").

    Concrete example: Imagine `lib_problem` is our upstream and `course_problem` is our downstream.

     * Say that the customizable fields are [display_name, max_attempts].

     * Set `course_problem.upstream_display_name = lib_problem.display_name` ("fetch").
     * If `not only_fetch`, and `course_problem.display_name` wasn't customized, then:
       * Set `course_problem.display_name = lib_problem.display_name` ("sync").
    """
    syncable_field_names = _get_synchronizable_fields(upstream, downstream)

    for field_name, fetch_field_name in downstream.get_customizable_fields().items():

        if field_name not in syncable_field_names:
            continue

        # Downstream-only fields don't have an upstream fetch field
        if fetch_field_name is None:
            continue

        # FETCH the upstream's value and save it on the downstream (ie, `downstream.upstream_$FIELD`).
        old_upstream_value = getattr(downstream, fetch_field_name)
        new_upstream_value = getattr(upstream, field_name)
        setattr(downstream, fetch_field_name, new_upstream_value)

        if only_fetch:
            continue

        # Okay, now for the nuanced part...
        # We need to update the downstream field *iff it has not been customized**.
        # Determining whether a field has been customized will differ in Beta vs Future release.
        # (See "PRESERVING DOWNSTREAM CUSTOMIZATIONS" comment below for details.)

        ## FUTURE BEHAVIOR: field is "customized" iff we have noticed that the user edited it.
        #  if field_name in downstream.downstream_customized:
        #      continue

        ## BETA BEHAVIOR: field is "customized" iff we have the prev upstream value, but field doesn't match it.
        downstream_value = getattr(downstream, field_name)
        if old_upstream_value and downstream_value != old_upstream_value:
            continue  # Field has been customized. Don't touch it. Move on.

        # Field isn't customized -- SYNC it!
        setattr(downstream, field_name, new_upstream_value)


def _update_non_customizable_fields(*, upstream: XBlock, downstream: XBlock) -> None:
    """
    For each field `downstream.blah` that isn't customizable: set it to `upstream.blah`.
    """
    syncable_fields = _get_synchronizable_fields(upstream, downstream)
    customizable_fields = set(downstream.get_customizable_fields().keys())
    # TODO: resolve this so there's no special-case happening for video block.
    # e.g. by some non_cloneable_fields property of the XBlock class?
    is_video_block = downstream.usage_key.block_type == "video"
    for field_name in syncable_fields - customizable_fields:
        if is_video_block and field_name == 'edx_video_id':
            # Avoid overwriting edx_video_id between blocks
            continue
        new_upstream_value = getattr(upstream, field_name)
        setattr(downstream, field_name, new_upstream_value)


def _update_tags(*, upstream: XBlock, downstream: XBlock) -> None:
    """
    Update tags from `upstream` to `downstream`
    """
    from openedx.core.djangoapps.content_tagging.api import copy_tags_as_read_only
    # For any block synced with an upstream, copy the tags as read_only
    # This keeps tags added locally.
    copy_tags_as_read_only(
        str(upstream.location),
        str(downstream.location),
    )


def _get_synchronizable_fields(upstream: XBlock, downstream: XBlock) -> set[str]:
    """
    The syncable fields are the ones which are content- or settings-scoped AND are defined on both (up,down)stream.
    """
    return set.intersection(*[
        set(
            field_name
            for (field_name, field) in block.__class__.fields.items()
            if field.scope in [Scope.settings, Scope.content]
        )
        for block in [upstream, downstream]
    ])
