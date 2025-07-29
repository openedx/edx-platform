"""
Content libraries data classes related to Containers.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from opaque_keys.edx.locator import LibraryContainerLocator, LibraryLocatorV2
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import Container

from openedx.core.djangoapps.content_tagging.api import get_object_tag_counts

from .libraries import PublishableItem

# The public API is only the following symbols:
__all__ = [
    # Models
    "ContainerMetadata",
    "ContainerType",
    # Methods
    "library_container_locator",
]


class ContainerType(Enum):
    """
    The container types supported by content_libraries, and logic to map them to OLX.
    """
    Unit = "unit"
    Subsection = "subsection"
    Section = "section"

    @property
    def olx_tag(self) -> str:
        """
        Canonical XML tag to use when representing this container as OLX.

        For example, Units are encoded as <vertical>...</vertical>.

        These tag names are historical. We keep them around for the backwards compatibility of OLX
        and for easier interaction with legacy modulestore-powered structural XBlocks
        (e.g., copy-paste of Units between courses and V2 libraries).
        """
        match self:
            case self.Unit:
                return "vertical"
            case self.Subsection:
                return "sequential"
            case self.Section:
                return "chapter"
        raise TypeError(f"unexpected ContainerType: {self!r}")

    @classmethod
    def from_source_olx_tag(cls, olx_tag: str) -> 'ContainerType':
        """
        Get the ContainerType that this OLX tag maps to.
        """
        if olx_tag == "unit":
            # There is an alternative implementation to VerticalBlock called UnitBlock whose
            # OLX tag is <unit>. When converting from OLX, we want to handle both <vertical>
            # and <unit> as Unit containers, although the canonical serialization is still <vertical>.
            return cls.Unit
        try:
            return next(ct for ct in cls if olx_tag == ct.olx_tag)
        except StopIteration:
            raise ValueError(f"no container_type for XML tag: <{olx_tag}>") from None


@dataclass(frozen=True, kw_only=True)
class ContainerMetadata(PublishableItem):
    """
    Class that represents the metadata about a Container (e.g. Unit) in a content library.
    """
    container_key: LibraryContainerLocator
    container_type: ContainerType
    container_pk: int

    @classmethod
    def from_container(cls, library_key, container: Container, associated_collections=None):
        """
        Construct a ContainerMetadata object from a Container object.
        """
        last_publish_log = container.versioning.last_publish_log
        container_key = library_container_locator(
            library_key,
            container=container,
        )
        container_type = ContainerType(container_key.container_type)
        published_by = ""
        if last_publish_log and last_publish_log.published_by:
            published_by = last_publish_log.published_by.username

        draft = container.versioning.draft
        published = container.versioning.published
        last_draft_created = draft.created if draft else None
        if draft and draft.publishable_entity_version.created_by:
            last_draft_created_by = draft.publishable_entity_version.created_by.username
        else:
            last_draft_created_by = ""
        tags = get_object_tag_counts(str(container_key), count_implicit=True)

        return cls(
            container_key=container_key,
            container_type=container_type,
            container_pk=container.pk,
            display_name=draft.title,
            created=container.created,
            modified=draft.created,
            draft_version_num=draft.version_num,
            published_version_num=published.version_num if published else None,
            published_display_name=published.title if published else None,
            last_published=None if last_publish_log is None else last_publish_log.published_at,
            published_by=published_by,
            last_draft_created=last_draft_created,
            last_draft_created_by=last_draft_created_by,
            has_unpublished_changes=authoring_api.contains_unpublished_changes(container.pk),
            tags_count=tags.get(str(container_key), 0),
            collections=associated_collections or [],
        )


def library_container_locator(
    library_key: LibraryLocatorV2,
    container: Container,
) -> LibraryContainerLocator:
    """
    Returns a LibraryContainerLocator for the given library + container.
    """
    container_type = None
    if hasattr(container, 'unit'):
        container_type = ContainerType.Unit
    elif hasattr(container, 'subsection'):
        container_type = ContainerType.Subsection
    elif hasattr(container, 'section'):
        container_type = ContainerType.Section
    else:
        # This should never happen, but we assert to ensure that we handle all cases.
        # If this fails, it means that a new Container type was added without updating this code.
        raise ValueError(f"Unexpected container type: {container!r}")

    return LibraryContainerLocator(
        library_key,
        container_type=container_type.value,
        container_id=container.publishable_entity.key,
    )
