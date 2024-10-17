"""
Synchronize content and settings from upstream blocks to their downstream usages.

At the time of writing, we assume that for any upstream-downstream linkage:
* The upstream is a Component from a Learning Core-backed Content Library.
* The downstream is a block of matching type in a SplitModuleStore-backed Course.
* They are both on the same Open edX instance.

HOWEVER, those assumptions may loosen in the future. So, we consider these to be INTERNAL ASSUMPIONS that should not be
exposed through this module's public Python interface.
"""
from __future__ import annotations

import logging
import typing as t
from dataclasses import dataclass, asdict

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import NotFound
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryUsageLocatorV2
from xblock.exceptions import XBlockNotFoundError
from xblock.fields import Scope, String, Integer
from xblock.core import XBlockMixin, XBlock

if t.TYPE_CHECKING:
    from django.contrib.auth.models import User  # pylint: disable=imported-auth-user


logger = logging.getLogger(__name__)


class UpstreamLinkException(Exception):
    """
    Raised whenever we try to inspect, sync-from, fetch-from, or delete a block's link to upstream content.

    There are three flavors (defined below): BadDownstream, BadUpstream, NoUpstream.

    Should be constructed with a human-friendly, localized, PII-free message, suitable for API responses and UI display.
    For now, at least, the message can assume that upstreams are Content Library blocks and downstreams are Course
    blocks, although that may need to change (see module docstring).
    """


class BadDownstream(UpstreamLinkException):
    """
    Downstream content does not support sync.
    """


class BadUpstream(UpstreamLinkException):
    """
    Reference to upstream content is malformed, invalid, and/or inaccessible.
    """


class NoUpstream(UpstreamLinkException):
    """
    The downstream content does not have an upstream link at all (...as is the case for most XBlocks usages).

    (This isn't so much an "error" like the other two-- it's just a case that needs to be handled exceptionally,
     usually by logging a message and then doing nothing.)
    """
    def __init__(self):
        super().__init__(_("Content is not linked to a Content Library."))


@dataclass(frozen=True)
class UpstreamLink:
    """
    Metadata about some downstream content's relationship with its linked upstream content.
    """
    upstream_ref: str | None  # Reference to the upstream content, e.g., a serialized library block usage key.
    version_synced: int | None  # Version of the upstream to which the downstream was last synced.
    version_available: int | None  # Latest version of the upstream that's available, or None if it couldn't be loaded.
    version_declined: int | None  # Latest version which the user has declined to sync with, if any.
    error_message: str | None  # If link is valid, None. Otherwise, a localized, human-friendly error message.

    @property
    def ready_to_sync(self) -> bool:
        """
        Should we invite the downstream's authors to sync the latest upstream updates?
        """
        return bool(
            self.upstream_ref and
            self.version_available and
            self.version_available > (self.version_synced or 0) and
            self.version_available > (self.version_declined or 0)
        )

    def to_json(self) -> dict[str, t.Any]:
        """
        Get an JSON-API-friendly representation of this upstream link.
        """
        return {
            **asdict(self),
            "ready_to_sync": self.ready_to_sync,
        }

    @classmethod
    def try_get_for_block(cls, downstream: XBlock) -> t.Self:
        """
        Same as `get_for_block`, but upon failure, sets `.error_message` instead of raising an exception.
        """
        try:
            return cls.get_for_block(downstream)
        except UpstreamLinkException as exc:
            logger.exception(
                "Tried to inspect an unsupported, broken, or missing downstream->upstream link: '%s'->'%s'",
                downstream.usage_key,
                downstream.upstream,
            )
            return cls(
                upstream_ref=downstream.upstream,
                version_synced=downstream.upstream_version,
                version_available=None,
                version_declined=None,
                error_message=str(exc),
            )

    @classmethod
    def get_for_block(cls, downstream: XBlock) -> t.Self:
        """
        Get info on a block's relationship with its linked upstream content (without actually loading the content).

        Currently, the only supported upstreams are LC-backed Library Components. This may change in the future (see
        module docstring).

        If link exists, is supported, and is followable, returns UpstreamLink.
        Otherwise, raises an UpstreamLinkException.
        """
        if not downstream.upstream:
            raise NoUpstream()
        if not isinstance(downstream.usage_key.context_key, CourseKey):
            raise BadDownstream(_("Cannot update content because it does not belong to a course."))
        if downstream.has_children:
            raise BadDownstream(_("Updating content with children is not yet supported."))
        try:
            upstream_key = LibraryUsageLocatorV2.from_string(downstream.upstream)
        except InvalidKeyError as exc:
            raise BadUpstream(_("Reference to linked library item is malformed")) from exc
        downstream_type = downstream.usage_key.block_type
        if upstream_key.block_type != downstream_type:
            # Note: Currently, we strictly enforce that the downstream and upstream block_types must exactly match.
            #       It could be reasonable to relax this requirement in the future if there's product need for it.
            #       For example, there's no reason that a StaticTabBlock couldn't take updates from an HtmlBlock.
            raise BadUpstream(
                _("Content type mismatch: {downstream_type} cannot be linked to {upstream_type}.").format(
                    downstream_type=downstream_type, upstream_type=upstream_key.block_type
                )
            ) from TypeError(
                f"downstream block '{downstream.usage_key}' is linked to "
                f"upstream block of different type '{upstream_key}'"
            )
        # We import this here b/c UpstreamSyncMixin is used by cms/envs, which loads before the djangoapps are ready.
        from openedx.core.djangoapps.content_libraries.api import (
            get_library_block  # pylint: disable=wrong-import-order
        )
        try:
            lib_meta = get_library_block(upstream_key)
        except XBlockNotFoundError as exc:
            raise BadUpstream(_("Linked library item was not found in the system")) from exc
        return cls(
            upstream_ref=downstream.upstream,
            version_synced=downstream.upstream_version,
            version_available=(lib_meta.draft_version_num if lib_meta else None),
            # TODO: Previous line is wrong. It should use the published version instead, but the
            # LearningCoreXBlockRuntime APIs do not yet support published content yet.
            # Will be fixed in a follow-up task: https://github.com/openedx/edx-platform/issues/35582
            # version_available=(lib_meta.published_version_num if lib_meta else None),
            version_declined=downstream.upstream_version_declined,
            error_message=None,
        )


def sync_from_upstream(downstream: XBlock, user: User) -> None:
    """
    Update `downstream` with content+settings from the latest available version of its linked upstream content.

    Preserves overrides to customizable fields; overwrites overrides to other fields.
    Does not save `downstream` to the store. That is left up to the caller.

    If `downstream` lacks a valid+supported upstream link, this raises an UpstreamLinkException.
    """
    link, upstream = _load_upstream_link_and_block(downstream, user)
    _update_customizable_fields(upstream=upstream, downstream=downstream, only_fetch=False)
    _update_non_customizable_fields(upstream=upstream, downstream=downstream)
    downstream.upstream_version = link.version_available


def fetch_customizable_fields(*, downstream: XBlock, user: User, upstream: XBlock | None = None) -> None:
    """
    Fetch upstream-defined value of customizable fields and save them on the downstream.

    If `upstream` is provided, use that block as the upstream.
    Otherwise, load the block specified by  `downstream.upstream`, which may raise an UpstreamLinkException.
    """
    if not upstream:
        _link, upstream = _load_upstream_link_and_block(downstream, user)
    _update_customizable_fields(upstream=upstream, downstream=downstream, only_fetch=True)


def _load_upstream_link_and_block(downstream: XBlock, user: User) -> tuple[UpstreamLink, XBlock]:
    """
    Load the upstream metadata and content for a downstream block.

    Assumes that the upstream content is an XBlock in an LC-backed content libraries. This assumption may need to be
    relaxed in the future (see module docstring).

    If `downstream` lacks a valid+supported upstream link, this raises an UpstreamLinkException.
    """
    link = UpstreamLink.get_for_block(downstream)  # can raise UpstreamLinkException
    # We import load_block here b/c UpstreamSyncMixin is used by cms/envs, which loads before the djangoapps are ready.
    from openedx.core.djangoapps.xblock.api import load_block  # pylint: disable=wrong-import-order
    try:
        lib_block: XBlock = load_block(LibraryUsageLocatorV2.from_string(downstream.upstream), user)
    except (NotFound, PermissionDenied) as exc:
        raise BadUpstream(_("Linked library item could not be loaded: {}").format(downstream.upstream)) from exc
    return link, lib_block


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

     * Set `course_problem.upstream_max_attempts = lib_problem.max_attempts` ("fetch").
     * If `not only_fetch`, and `course_problem.max_attempts` wasn't customized, then:
       * Set `course_problem.max_attempts = lib_problem.max_attempts` ("sync").
    """
    syncable_field_names = _get_synchronizable_fields(upstream, downstream)

    for field_name, fetch_field_name in downstream.get_customizable_fields().items():

        if field_name not in syncable_field_names:
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
    for field_name in syncable_fields - customizable_fields:
        new_upstream_value = getattr(upstream, field_name)
        setattr(downstream, field_name, new_upstream_value)


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


def decline_sync(downstream: XBlock) -> None:
    """
    Given an XBlock that is linked to upstream content, mark the latest available update as 'declined' so that its
    authors are not prompted (until another upstream version becomes available).

    Does not save `downstream` to the store. That is left up to the caller.

    If `downstream` lacks a valid+supported upstream link, this raises an UpstreamLinkException.
    """
    upstream_link = UpstreamLink.get_for_block(downstream)  # Can raise UpstreamLinkException
    downstream.upstream_version_declined = upstream_link.version_available


def sever_upstream_link(downstream: XBlock) -> None:
    """
    Given an XBlock that is linked to upstream content, disconnect the link, such that authors are never again prompted
    to sync upstream updates. Erase all `.upstream*` fields from the downtream block.

    However, before nulling out the `.upstream` field, we copy its value over to `.copied_from_block`. This makes sense,
    because once a downstream block has been de-linked from source (e.g., a Content Library block), it is no different
    than if the block had just been copy-pasted in the first place.

    Does not save `downstream` to the store. That is left up to the caller.

    If `downstream` lacks a link, then this raises NoUpstream (though it is reasonable for callers to handle such
    exception and ignore it, as the end result is the same: `downstream.upstream is None`).
    """
    if not downstream.upstream:
        raise NoUpstream()
    downstream.copied_from_block = downstream.upstream
    downstream.upstream = None
    downstream.upstream_version = None
    for _, fetched_upstream_field in downstream.get_customizable_fields().items():
        setattr(downstream, fetched_upstream_field, None)  # Null out upstream_display_name, et al.


class UpstreamSyncMixin(XBlockMixin):
    """
    Allows an XBlock in the CMS to be associated & synced with an upstream.

    Mixed into CMS's XBLOCK_MIXINS, but not LMS's.
    """

    # Upstream synchronization metadata fields
    upstream = String(
        help=(
            "The usage key of a block (generally within a content library) which serves as a source of upstream "
            "updates for this block, or None if there is no such upstream. Please note: It is valid for this "
            "field to hold a usage key for an upstream block that does not exist (or does not *yet* exist) on "
            "this instance, particularly if this downstream block was imported from a different instance."
        ),
        default=None, scope=Scope.settings, hidden=True, enforce_type=True
    )
    upstream_version = Integer(
        help=(
            "Record of the upstream block's version number at the time this block was created from it. If this "
            "upstream_version is smaller than the upstream block's latest published version, then the author will be "
            "invited to sync updates into this downstream block, presuming that they have not already declined to sync "
            "said version."
        ),
        default=None, scope=Scope.settings, hidden=True, enforce_type=True,
    )
    upstream_version_declined = Integer(
        help=(
            "Record of the latest upstream version for which the author declined to sync updates, or None if they have "
            "never declined an update."
        ),
        default=None, scope=Scope.settings, hidden=True, enforce_type=True,
    )

    # Store the fetched upstream values for customizable fields.
    upstream_display_name = String(
        help=("The value of display_name on the linked upstream block."),
        default=None, scope=Scope.settings, hidden=True, enforce_type=True,
    )
    upstream_max_attempts = Integer(
        help=("The value of max_attempts on the linked upstream block."),
        default=None, scope=Scope.settings, hidden=True, enforce_type=True,
    )

    @classmethod
    def get_customizable_fields(cls) -> dict[str, str]:
        """
        Mapping from each customizable field to the field which can be used to restore its upstream value.

        XBlocks outside of edx-platform can override this in order to set up their own customizable fields.
        """
        return {
            "display_name": "upstream_display_name",
            "max_attempts": "upstream_max_attempts",
        }

    # PRESERVING DOWNSTREAM CUSTOMIZATIONS and RESTORING UPSTREAM VALUES
    #
    # For the full Content Libraries Relaunch, we would like to keep track of which customizable fields the user has
    # actually customized. The idea is: once an author has customized a customizable field....
    #
    #   - future upstream syncs will NOT blow away the customization,
    #   - but future upstream syncs WILL fetch the upstream values and tuck them away in a hidden field,
    #   - and the author can can revert back to said fetched upstream value at any point.
    #
    # Now, whether field is "customized" (and thus "revertible") is dependent on whether they have ever edited it.
    # To instrument this, we need to keep track of which customizable fields have been edited using a new XBlock field:
    # `downstream_customized`
    #
    # Implementing `downstream_customized` has proven difficult, because there is no simple way to keep it up-to-date
    # with the many different ways XBlock fields can change. The `.save()` and `.editor_saved()` methods are promising,
    # but we need to do more due diligence to be sure that they cover all cases, including API edits, import/export,
    # copy/paste, etc. We will figure this out in time for the full Content Libraries Relaunch (related ticket:
    # https://github.com/openedx/frontend-app-authoring/issues/1317). But, for the Beta realease, we're going to
    # implement something simpler:
    #
    # - We fetch upstream values for customizable fields and tuck them away in a hidden field (same as above).
    # - If a customizable field DOES match the fetched upstream value, then future upstream syncs DO update it.
    # - If a customizable field does NOT the fetched upstream value, then future upstream syncs DO NOT update it.
    # - There is no UI option for explicitly reverting back to the fetched upstream value.
    #
    # For future reference, here is a partial implementation of what we are thinking for the full Content Libraries
    # Relaunch::
    #
    #    downstream_customized = List(
    #        help=(
    #            "Names of the fields which have values set on the upstream block yet have been explicitly "
    #            "overridden on this downstream block. Unless explicitly cleared by the user, these customizations "
    #            "will persist even when updates are synced from the upstream."
    #        ),
    #        default=[], scope=Scope.settings, hidden=True, enforce_type=True,
    #    )
    #
    #    def save(self, *args, **kwargs):
    #        """
    #        Update `downstream_customized` when a customizable field is modified.
    #
    #        NOTE: This does not work, because save() isn't actually called in all the cases that we'd want it to be.
    #        """
    #        super().save(*args, **kwargs)
    #        customizable_fields = self.get_customizable_fields()
    #
    #        # Loop through all the fields that are potentially cutomizable.
    #        for field_name, restore_field_name in self.get_customizable_fields():
    #
    #            # If the field is already marked as customized, then move on so that we don't
    #            # unneccessarily query the block for its current value.
    #            if field_name in self.downstream_customized:
    #                continue
    #
    #            # If this field's value doesn't match the synced upstream value, then mark the field
    #            # as customized so that we don't clobber it later when syncing.
    #            # NOTE: Need to consider the performance impact of all these field lookups.
    #            if getattr(self, field_name) != getattr(self, restore_field_name):
    #                self.downstream_customized.append(field_name)
