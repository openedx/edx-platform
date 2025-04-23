"""
Synchronize content and settings from upstream containers to their downstream usages.

* The upstream is a Container from a Learning Core-backed Content Library.
* The downstream is a block of matching type in a SplitModuleStore-backed Course.
* They are both on the same Open edX instance.

HOWEVER, those assumptions may loosen in the future. So, we consider these to be INTERNAL ASSUMPIONS that should not be
exposed through this module's public Python interface.
"""

import logging
import typing as t
from dataclasses import asdict, dataclass

from django.conf import settings
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import LibraryContainerLocator
from rest_framework.exceptions import NotFound
from xblock.core import XBlock
from xblock.fields import Scope

from cms.djangoapps.contentstore.xblock_storage_handlers.create_xblock import create_xblock
from openedx.core.djangoapps.content_libraries.api import get_container_children

from .upstream_sync import (
    BadUpstream,
    BaseUpstreamLink,
    BaseUpstreamSyncManager,
    UpstreamLinkException,
    check_and_parse_upstream_key,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContainerUpstreamLink(BaseUpstreamLink):
    """
    Metadata about some downstream content's relationship with its linked upstream content.
    """

    @property
    def upstream_link(self) -> str | None:
        """
        Link to edit/view upstream block in library.
        """
        if self.version_available is None or self.upstream_ref is None:
            return None
        try:
            container_key = LibraryContainerLocator.from_string(self.upstream_ref)
        except InvalidKeyError:
            return None
        return _get_library_container_url(container_key)

    def to_json(self) -> dict[str, t.Any]:
        """
        Get an JSON-API-friendly representation of this upstream link.
        """
        return {
            **asdict(self),
            "ready_to_sync": self.ready_to_sync,
            "upstream_link": self.upstream_link,
        }

    @classmethod
    def get_for_container(cls, downstream: XBlock) -> t.Self:
        """
        Get info on a container's relationship with its linked upstream content (without actually loading the content).

        Currently, the only supported upstreams are LC-backed Library Components. This may change in the future (see
        module docstring).

        If link exists, is supported, and is followable, returns UpstreamLink.
        Otherwise, raises an UpstreamLinkException.
        """
        upstream_key = check_and_parse_upstream_key(downstream.upstream, downstream.usage_key)
        # We import this here b/c UpstreamSyncMixin is used by cms/envs, which loads before the djangoapps are ready.
        from openedx.core.djangoapps.content_libraries.api import (
            ContentLibraryContainerNotFound,  # pylint: disable=wrong-import-order
            get_container,  # pylint: disable=wrong-import-order
        )
        if not isinstance(upstream_key, LibraryContainerLocator):
            raise BadUpstream(_("Invalid upstream_key"))
        try:
            lib_meta = get_container(upstream_key)
        except ContentLibraryContainerNotFound as exc:
            raise BadUpstream(_("Linked library item was not found in the system")) from exc
        return cls(
            upstream_ref=downstream.upstream,
            version_synced=downstream.upstream_version,
            version_available=(lib_meta.published_version_num if lib_meta else None),
            version_declined=downstream.upstream_version_declined,
            error_message=None,
        )

    @classmethod
    def try_get_for_container(cls, downstream: XBlock) -> t.Self:
        """
        Same as `get_for_container`, but upon failure, sets `.error_message` instead of raising an exception.
        """
        try:
            return cls.get_for_container(downstream)
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


def _get_library_container_url(container_key: LibraryContainerLocator):
    """
    Gets authoring url for given library_key.
    """
    library_url = None
    if mfe_base_url := settings.COURSE_AUTHORING_MICROFRONTEND_URL:  # type: ignore
        library_key = container_key.context_key
        library_url = f'{mfe_base_url}/library/{library_key}/units?container_key={container_key}'
    return library_url


class ContainerUpstreamSyncManager(BaseUpstreamSyncManager):
    """
    Manages sync process of downstream containers like unit with upstream containers.
    """
    def __init__(self, downstream: XBlock, user: User, upstream: XBlock | None = None) -> None:
        super().__init__(downstream, user, upstream)
        if not isinstance(self.upstream_key, LibraryContainerLocator):
            raise BadUpstream('Invalid upstream key')
        if not upstream:
            self.link = ContainerUpstreamLink.get_for_container(downstream)
            self.upstream = self._load_upstream_link_and_container_block()
        self.syncable_field_names: set[str] = self._get_synchronizable_fields()
        self.new_children_blocks: list[XBlock] = []

    def _get_synchronizable_fields(self) -> set[str]:
        """
        The syncable fields are the ones which are content- or settings-scoped AND are defined on both (up,down)stream.
        """
        return set.intersection(*[
            set(
                field_name
                for (field_name, field) in block.__class__.fields.items()
                if field.scope in [Scope.settings, Scope.content]
            )
            for block in [self.upstream, self.downstream]
        ])

    def _load_upstream_link_and_container_block(self) -> XBlock:
        """
        Load the upstream metadata and content for a downstream block.

        Assumes that the upstream content is an XBlock in an LC-backed content libraries. This assumption may need to be
        relaxed in the future (see module docstring).

        If `downstream` lacks a valid+supported upstream link, this raises an UpstreamLinkException.
        """
        # We import load_block here b/c UpstreamSyncMixin is used by cms/envs,
        # which loads before the djangoapps are ready.
        from openedx.core.djangoapps.xblock.api import (  # pylint: disable=wrong-import-order
            CheckPerm,
            LatestVersion,
            load_block,
        )
        try:
            lib_block: XBlock = load_block(
                self.upstream_key,
                self.user,
                check_permission=CheckPerm.CAN_READ_AS_AUTHOR,
                version=LatestVersion.PUBLISHED,
            )
        except (NotFound, PermissionDenied) as exc:
            raise BadUpstream(_("Linked library item could not be loaded: {}").format(self.upstream_key)) from exc
        return lib_block

    def sync_new_children_blocks(self):
        """
        Creates children xblocks in course based on library container children.
        """
        for child in get_container_children(self.upstream_key, published=True):
            child_block = create_xblock(
                parent_locator=str(self.downstream.location),
                user=self.user,
                category=child.usage_key.block_type,
                display_name=child.display_name,
            )
            child_block.upstream = str(child.usage_key)
            self.new_children_blocks.append(child_block)
        return self.new_children_blocks

    def delete_extra_blocks(self):
        """
        Deletes extra child blocks under the container that are not present in new version of library container.
        """
        # TODO: Importing here to avoid circular imports, should be fixed later
        from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import delete_item
        current = self.downstream.children
        latest = [str(child.usage_key) for child in get_container_children(self.upstream_key, published=True)]
        for child in current:
            # TODO: doesn't work for two reasons
            # 1. child is not an XBlock but usage_key, so we need to load the child to get its upstream
            # 2. Even if we get child, it won't have upstream set as we are not setting upstream for child components
            #    See: cms/djangoapps/contentstore/xblock_storage_handlers/view_handlers.py:535
            if child.upstream not in latest:
                delete_item(self.user, child.usage_key)

    def sync(self) -> None:
        super().sync()
        # self.delete_extra_blocks()
        self.sync_new_children_blocks()


def sync_from_upstream_container(downstream: XBlock, user: User) -> tuple[XBlock, list[XBlock]]:
    """
    Update `downstream` with content+settings from the latest available version of its linked upstream content.

    Preserves overrides to customizable fields; overwrites overrides to other fields.
    Does not save `downstream` to the store. That is left up to the caller.

    If `downstream` lacks a valid+supported upstream link, this raises an UpstreamLinkException.
    """
    manager = ContainerUpstreamSyncManager(downstream, user)
    manager.sync()
    downstream.upstream_version = manager.link.version_available
    return manager.upstream, manager.new_children_blocks
