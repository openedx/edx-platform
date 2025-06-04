"""
Synchronize content and settings from upstream content to their downstream
usages.

At the time of writing, we assume that for any upstream-downstream linkage:
* The upstream is a Component or Container from a Learning Core-backed Content
  Library.
* The downstream is a block of compatible type in a SplitModuleStore-backed
  Course.
* They are both on the same Open edX instance.

HOWEVER, those assumptions may loosen in the future. So, we consider these to be
INTERNAL ASSUMPIONS that should not be exposed through this module's public
Python interface.
"""
from __future__ import annotations

import logging
import typing as t
from dataclasses import dataclass, asdict

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryContainerLocator, LibraryUsageLocatorV2
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
    upstream_key: LibraryUsageLocatorV2 | LibraryContainerLocator | None  # parsed opaque key version of upstream_ref
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

    @property
    def upstream_link(self) -> str | None:
        """
        Link to edit/view upstream block in library.
        """
        if self.version_available is None or self.upstream_key is None:
            return None
        if isinstance(self.upstream_key, LibraryUsageLocatorV2):
            return _get_library_xblock_url(self.upstream_key)
        if isinstance(self.upstream_key, LibraryContainerLocator):
            return _get_library_container_url(self.upstream_key)
        return None

    def to_json(self) -> dict[str, t.Any]:
        """
        Get an JSON-API-friendly representation of this upstream link.
        """
        data = {
            **asdict(self),
            "ready_to_sync": self.ready_to_sync,
            "upstream_link": self.upstream_link,
        }
        del data["upstream_key"]  # As JSON (string), this would be redundant with upstream_ref
        return data

    @classmethod
    def try_get_for_block(cls, downstream: XBlock, log_error: bool = True) -> t.Self:
        """
        Same as `get_for_block`, but upon failure, sets `.error_message` instead of raising an exception.
        """
        try:
            return cls.get_for_block(downstream)
        except UpstreamLinkException as exc:
            # Note: if we expect that an upstream may not be set at all (i.e. we're just inspecting a random
            # unit that may be a regular course unit), we don't want to log this, so set log_error=False then.
            if log_error:
                logger.exception(
                    "Tried to inspect an unsupported, broken, or missing downstream->upstream link: '%s'->'%s'",
                    downstream.usage_key,
                    downstream.upstream,
                )
            return cls(
                upstream_ref=getattr(downstream, "upstream", ""),
                upstream_key=None,
                version_synced=getattr(downstream, "upstream_version", None),
                version_available=None,
                version_declined=None,
                error_message=str(exc),
            )

    @classmethod
    def get_for_block(cls, downstream: XBlock) -> t.Self:
        """
        Get info on a downstream block's relationship with its linked upstream
        content (without actually loading the content).

        Currently, the only supported upstreams are LC-backed Library Components
        (XBlocks) or Containers. This may change in the future (see module
        docstring).

        If link exists, is supported, and is followable, returns UpstreamLink.
        Otherwise, raises an UpstreamLinkException.
        """
        # We import this here b/c UpstreamSyncMixin is used by cms/envs, which loads before the djangoapps are ready.
        from openedx.core.djangoapps.content_libraries import api as lib_api

        if not isinstance(downstream, UpstreamSyncMixin):
            raise BadDownstream(_("Downstream is not an XBlock or is missing required UpstreamSyncMixin"))
        if not downstream.upstream:
            raise NoUpstream()
        if not isinstance(downstream.usage_key.context_key, CourseKey):
            raise BadDownstream(_("Cannot update content because it does not belong to a course."))
        downstream_type = downstream.usage_key.block_type

        upstream_key: LibraryUsageLocatorV2 | LibraryContainerLocator
        try:
            upstream_key = LibraryUsageLocatorV2.from_string(downstream.upstream)
        except InvalidKeyError:
            try:
                upstream_key = LibraryContainerLocator.from_string(downstream.upstream)
            except InvalidKeyError as exc:
                raise BadUpstream(_("Reference to linked library item is malformed")) from exc

        if isinstance(upstream_key, LibraryUsageLocatorV2):
            # The upstream is an XBlock
            if downstream.has_children:
                raise BadDownstream(
                    _("Updating content with children is not yet supported unless the upstream is a container."),
                )
            expected_downstream_block_type = upstream_key.block_type
            try:
                block_meta = lib_api.get_library_block(upstream_key)
            except XBlockNotFoundError as exc:
                raise BadUpstream(_("Linked upstream library block was not found in the system")) from exc
            version_available = block_meta.published_version_num
        else:
            # The upstream is a Container:
            assert isinstance(upstream_key, LibraryContainerLocator)
            try:
                container_meta = lib_api.get_container(upstream_key)
            except lib_api.ContentLibraryContainerNotFound as exc:
                raise BadUpstream(_("Linked upstream library container was not found in the system")) from exc
            expected_downstream_block_type = container_meta.container_type.olx_tag
            version_available = container_meta.published_version_num

        if downstream_type != expected_downstream_block_type:
            # Note: generally the upstream and downstream types must match, except that upstream containers
            # may have e.g. container_type=unit while the downstream block has the equivalent block_type=vertical.
            # It could be reasonable to relax this requirement in the future if there's product need for it.
            # for example, there's no reason that a StaticTabBlock couldn't take updates from an HtmlBlock.
            raise BadUpstream(
                _(
                    "Content type mismatch: {downstream_id} ({downstream_type}) cannot be linked to {upstream_id}."
                ).format(
                    downstream_id=downstream.usage_key,
                    downstream_type=downstream_type,
                    upstream_id=str(upstream_key),
                )
            )

        return cls(
            upstream_ref=downstream.upstream,
            upstream_key=upstream_key,
            version_synced=downstream.upstream_version,
            version_available=version_available,
            version_declined=downstream.upstream_version_declined,
            error_message=None,
        )


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
        # Downstream-only fields don't have an upstream fetch field
        if fetched_upstream_field is None:
            continue
        setattr(downstream, fetched_upstream_field, None)  # Null out upstream_display_name, et al.


def _get_library_xblock_url(usage_key: LibraryUsageLocatorV2):
    """
    Gets authoring url for given library_key.
    """
    library_url = None
    if mfe_base_url := settings.COURSE_AUTHORING_MICROFRONTEND_URL:  # type: ignore
        library_key = usage_key.lib_key
        library_url = f'{mfe_base_url}/library/{library_key}/components?usageKey={usage_key}'
    return library_url


def _get_library_container_url(container_key: LibraryContainerLocator):
    """
    Gets authoring url for given container_key.
    """
    library_url = None
    if mfe_base_url := settings.COURSE_AUTHORING_MICROFRONTEND_URL:  # type: ignore
        library_key = container_key.lib_key
        if container_key.container_type == "unit":
            library_url = f'{mfe_base_url}/library/{library_key}/units/{container_key}'
    return library_url


class UpstreamSyncMixin(XBlockMixin):
    """
    Allows an XBlock in the CMS to be associated & synced with an upstream.

    Mixed into CMS's XBLOCK_MIXINS, but not LMS's.
    """

    # Upstream synchronization metadata fields
    upstream = String(
        help=(
            "The usage key or container key of the source block/container (generally within a content library) "
            "which serves as a source of upstream updates for this block, or None if there is no such upstream. "
            "Please note: It is valid for this field to hold a key for an upstream block/container that does not "
            "exist (or does not *yet* exist) on this instance, particularly if this downstream block was imported "
            "from a different instance."
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
        help=("The value of display_name on the linked upstream block/container."),
        default=None, scope=Scope.settings, hidden=True, enforce_type=True,
    )

    @classmethod
    def get_customizable_fields(cls) -> dict[str, str | None]:
        """
        Mapping from each customizable field to the field which can be used to restore its upstream value.

        If the customizable field is mapped to None, then it is considered "downstream only", and cannot be restored
        from the upstream value.

        XBlocks outside of edx-platform can override this in order to set up their own customizable fields.
        """
        return {
            "display_name": "upstream_display_name",
            "attempts_before_showanswer_button": None,
            "due": None,
            "force_save_button": None,
            "graceperiod": None,
            "grading_method": None,
            "max_attempts": None,
            "show_correctness": None,
            "show_reset_button": None,
            "showanswer": None,
            "submission_wait_seconds": None,
            "weight": None,
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
    #            # If there is no restore_field name, it's a downstream-only field
    #            if restore_field_name is None:
    #                continue
    #
    #            # If this field's value doesn't match the synced upstream value, then mark the field
    #            # as customized so that we don't clobber it later when syncing.
    #            # NOTE: Need to consider the performance impact of all these field lookups.
    #            if getattr(self, field_name) != getattr(self, restore_field_name):
    #                self.downstream_customized.append(field_name)
