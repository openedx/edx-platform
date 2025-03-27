"""
Dataclasses for Content library API
"""
from dataclasses import dataclass, field
from datetime import datetime

from django.contrib.auth.models import AbstractUser, Group

from opaque_keys.edx.locator import LibraryLocatorV2

from ..models import ContentLibraryPermission


class AccessLevel:
    """ Enum defining library access levels/permissions """
    ADMIN_LEVEL = ContentLibraryPermission.ADMIN_LEVEL
    AUTHOR_LEVEL = ContentLibraryPermission.AUTHOR_LEVEL
    READ_LEVEL = ContentLibraryPermission.READ_LEVEL
    NO_ACCESS = None


@dataclass(frozen=True)
class LibraryItem:
    """
    Common fields for anything that can be found in a content library.
    """
    created: datetime
    modified: datetime
    display_name: str


@dataclass(frozen=True)
class CollectionMetadata:
    """
    Class to represent collection metadata in a content library.
    """
    key: str
    title: str


@dataclass(frozen=True, kw_only=True)
class PublishableItem(LibraryItem):
    """
    Common fields for anything that can be found in a content library that has
    draft/publish support.
    """
    draft_version_num: int
    published_version_num: int | None = None
    last_published: datetime | None = None
    # The username of the user who last published this.
    published_by: str = ""
    last_draft_created: datetime | None = None
    # The username of the user who created the last draft.
    last_draft_created_by: str = ""
    has_unpublished_changes: bool = False
    collections: list[CollectionMetadata] = field(default_factory=list)


@dataclass(frozen=True)
class ContentLibraryMetadata:
    """
    Class that represents the metadata about a content library.
    """
    key: LibraryLocatorV2
    learning_package_id: int | None
    title: str = ""
    description: str = ""
    num_blocks: int = 0
    version: int = 0
    last_published: datetime | None = None
    # The username of the user who last published this
    published_by: str = ""
    last_draft_created: datetime | None = None
    # The username of the user who created the last draft.
    last_draft_created_by: str = ""
    has_unpublished_changes: bool = False
    # has_unpublished_deletes will be true when the draft version of the library's bundle
    # contains deletes of any XBlocks that were in the most recently published version
    has_unpublished_deletes: bool = False
    allow_lti: bool = False
    # Allow any user (even unregistered users) to view and interact directly
    # with this library's content in the LMS
    allow_public_learning: bool = False
    # Allow any user with Studio access to view this library's content in
    # Studio, use it in their courses, and copy content out of this library.
    allow_public_read: bool = False
    license: str = ""
    created: datetime | None = None
    updated: datetime | None = None


@dataclass(frozen=True)
class ContentLibraryPermissionEntry:
    """
    A user or group granted permission to use a content library.
    """
    user: AbstractUser | None = None
    group: Group | None = None
    access_level: str | None = AccessLevel.NO_ACCESS  # TODO: make this a proper enum?


@dataclass(frozen=True)
class LibraryXBlockStaticFile:
    """
    Class that represents a static file in a content library, associated with
    a particular XBlock.
    """
    # File path e.g. "diagram.png"
    # In some rare cases it might contain a folder part, e.g. "en/track1.srt"
    path: str
    # Publicly accessible URL where the file can be downloaded
    url: str
    # Size in bytes
    size: int


@dataclass(frozen=True)
class LibraryXBlockType:
    """
    An XBlock type that can be added to a content library
    """
    block_type: str
    display_name: str
