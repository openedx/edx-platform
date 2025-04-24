"""
Python API for content libraries
================================

Via ``views.py``, most of these API methods are also exposed as a REST API.

The API methods in this file are focused on authoring and specific to content
libraries; they wouldn't necessarily apply or work in other learning contexts
such as courses, blogs, "pathways," etc.

** As this is an authoring-focused API, all API methods in this file deal with
the DRAFT version of the content library.**

Some of these methods will work and may be used from the LMS if needed (mostly
for test setup; other use is discouraged), but some of the implementation
details rely on Studio so other methods will raise errors if called from the
LMS. (The REST API is not available at all from the LMS.)

Any APIs that use/affect content libraries but are generic enough to work in
other learning contexts too are in the core XBlock python/REST API at
``openedx.core.djangoapps.xblock.api/rest_api``.

For example, to render a content library XBlock as HTML, one can use the
generic:

    render_block_view(block, view_name, user)

That is an API in ``openedx.core.djangoapps.xblock.api`` (use it from Studio for
the draft version, from the LMS for published version).

There are one or two methods in this file that have some overlap with the core
XBlock API; for example, this content library API provides a
``get_library_block()`` which returns metadata about an XBlock; it's in this API
because it also returns data about whether or not the XBlock has unpublished
edits, which is an authoring-only concern.  Likewise, APIs for getting/setting
an individual XBlock's OLX directly seem more appropriate for small, reusable
components in content libraries and may not be appropriate for other learning
contexts so they are implemented here in the library API only.  In the future,
if we find a need for these in most other learning contexts then those methods
could be promoted to the core XBlock API and made generic.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime
import logging

from django.conf import settings
from django.contrib.auth.models import AbstractUser, AnonymousUser, Group
from django.core.exceptions import PermissionDenied
from django.core.validators import validate_unicode_slug
from django.db import IntegrityError, transaction
from django.db.models import Q, QuerySet
from django.utils.translation import gettext as _
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_events.content_authoring.data import (
    ContentLibraryData,
    LibraryCollectionData,
    ContentObjectChangedData,
)
from openedx_events.content_authoring.signals import (
    CONTENT_LIBRARY_CREATED,
    CONTENT_LIBRARY_DELETED,
    CONTENT_LIBRARY_UPDATED,
    LIBRARY_COLLECTION_UPDATED,
    CONTENT_OBJECT_ASSOCIATIONS_CHANGED,
)
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import Component
from organizations.models import Organization
from xblock.core import XBlock

from openedx.core.types import User as UserType

from .. import permissions
from ..constants import ALL_RIGHTS_RESERVED
from ..models import ContentLibrary, ContentLibraryPermission
from .collections import library_collection_locator
from .exceptions import (
    LibraryAlreadyExists,
    LibraryPermissionIntegrityError,
)

log = logging.getLogger(__name__)

# The public API is only the following symbols:
__all__ = [
    # Library Models
    "ContentLibrary",  # Should this be public or not?
    "ContentLibraryMetadata",
    "AccessLevel",
    "ContentLibraryPermissionEntry",
    "LibraryXBlockType",
    "CollectionMetadata",
    # Library API methods
    "user_can_create_library",
    "get_libraries_for_user",
    "get_metadata",
    "require_permission_for_library_key",
    "get_library",
    "create_library",
    "get_library_team",
    "get_library_user_permissions",
    "set_library_user_permissions",
    "set_library_group_permissions",
    "update_library",
    "delete_library",
    "library_component_usage_key",
    "get_allowed_block_types",
    "publish_changes",
    "revert_changes",
]


# Models
# ======


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


class AccessLevel:
    """ Enum defining library access levels/permissions """
    ADMIN_LEVEL = ContentLibraryPermission.ADMIN_LEVEL
    AUTHOR_LEVEL = ContentLibraryPermission.AUTHOR_LEVEL
    READ_LEVEL = ContentLibraryPermission.READ_LEVEL
    NO_ACCESS = None


@dataclass(frozen=True)
class ContentLibraryPermissionEntry:
    """
    A user or group granted permission to use a content library.
    """
    user: AbstractUser | None = None
    group: Group | None = None
    access_level: str | None = AccessLevel.NO_ACCESS  # TODO: make this a proper enum?


@dataclass(frozen=True)
class CollectionMetadata:
    """
    Class to represent collection metadata in a content library.
    """
    key: str
    title: str


@dataclass(frozen=True)
class LibraryItem:
    """
    Common fields for anything that can be found in a content library.
    """
    created: datetime
    modified: datetime
    display_name: str


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
    collections: list[CollectionMetadata] = dataclass_field(default_factory=list)
    can_stand_alone: bool = True


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


# General APIs
# ============


def user_can_create_library(user: AbstractUser) -> bool:
    """
    Check if the user has permission to create a content library.
    """
    return user.has_perm(permissions.CAN_CREATE_CONTENT_LIBRARY)


def get_libraries_for_user(user, org=None, text_search=None, order=None) -> QuerySet[ContentLibrary]:
    """
    Return content libraries that the user has permission to view.
    """
    filter_kwargs = {}
    if org:
        filter_kwargs['org__short_name'] = org
    qs = ContentLibrary.objects.filter(**filter_kwargs) \
                               .select_related('learning_package', 'org') \
                               .order_by('org__short_name', 'slug')

    if text_search:
        qs = qs.filter(
            Q(slug__icontains=text_search) |
            Q(org__short_name__icontains=text_search) |
            Q(learning_package__title__icontains=text_search) |
            Q(learning_package__description__icontains=text_search)
        )

    filtered = permissions.perms[permissions.CAN_VIEW_THIS_CONTENT_LIBRARY].filter(user, qs)

    if order:
        order_query = 'learning_package__'
        valid_order_fields = ['title', 'created', 'updated']
        # If order starts with a -, that means order descending (default is ascending)
        if order.startswith('-'):
            order_query = f"-{order_query}"
            order = order[1:]

        if order in valid_order_fields:
            return filtered.order_by(f"{order_query}{order}")
        else:
            log.exception(f"Error ordering libraries by {order}: Invalid order field")

    return filtered


def get_metadata(queryset: QuerySet[ContentLibrary], text_search: str | None = None) -> list[ContentLibraryMetadata]:
    """
    Take a list of ContentLibrary objects and return metadata from Learning Core.
    """
    if text_search:
        queryset = queryset.filter(org__short_name__icontains=text_search)

    libraries = [
        # TODO: Do we really need these fields for the library listing view?
        # It's actually going to be pretty expensive to compute this over a
        # large list. If we do need it, it might need to go into a denormalized
        # form, e.g. a new table for stats that it can join to, even if we don't
        # guarantee accuracy (because of possible race conditions).
        ContentLibraryMetadata(
            key=lib.library_key,
            title=lib.learning_package.title if lib.learning_package else "",
            description="",
            version=0,
            allow_public_learning=lib.allow_public_learning,
            allow_public_read=lib.allow_public_read,

            # These are currently dummy values to maintain the REST API contract
            # while we shift to Learning Core models.
            num_blocks=0,
            last_published=None,
            has_unpublished_changes=False,
            has_unpublished_deletes=False,
            license=lib.license,
            learning_package_id=lib.learning_package_id,
        )
        for lib in queryset
    ]
    return libraries


def require_permission_for_library_key(library_key: LibraryLocatorV2, user: UserType, permission) -> ContentLibrary:
    """
    Given any of the content library permission strings defined in
    openedx.core.djangoapps.content_libraries.permissions,
    check if the given user has that permission for the library with the
    specified library ID.

    Raises django.core.exceptions.PermissionDenied if the user doesn't have
    permission.
    """
    library_obj = ContentLibrary.objects.get_by_key(library_key)  # type: ignore[attr-defined]
    if not user.has_perm(permission, obj=library_obj):
        raise PermissionDenied

    return library_obj


def get_library(library_key: LibraryLocatorV2) -> ContentLibraryMetadata:
    """
    Get the library with the specified key. Does not check permissions.
    returns a ContentLibraryMetadata instance.

    Raises ContentLibraryNotFound if the library doesn't exist.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    learning_package = ref.learning_package
    assert learning_package is not None  # Shouldn't happen - this is just for the type checker
    num_blocks = authoring_api.get_all_drafts(learning_package.id).count()
    last_publish_log = authoring_api.get_last_publish(learning_package.id)
    last_draft_log = authoring_api.get_entities_with_unpublished_changes(learning_package.id) \
        .order_by('-created').first()
    last_draft_created = last_draft_log.created if last_draft_log else None
    last_draft_created_by = last_draft_log.created_by.username if last_draft_log and last_draft_log.created_by else ""
    has_unpublished_changes = last_draft_log is not None

    # TODO: I'm doing this one to match already-existing behavior, but this is
    # something that we should remove. It exists to accomodate some complexities
    # with how Blockstore staged changes, but Learning Core works differently,
    # and has_unpublished_changes should be sufficient.
    # Ref: https://github.com/openedx/edx-platform/issues/34283
    has_unpublished_deletes = authoring_api.get_entities_with_unpublished_deletes(learning_package.id) \
                                           .exists()

    # Learning Core doesn't really have a notion of a global version number,but
    # we can sort of approximate it by using the primary key of the last publish
    # log entry, in the sense that it will be a monotonically increasing
    # integer, though there will be large gaps. We use 0 to denote that nothing
    # has been done, since that will never be a valid value for a PublishLog pk.
    #
    # That being said, we should figure out if we really even want to keep a top
    # level version indicator for the Library as a whole. In the v1 libs
    # implemention, this served as a way to know whether or not there was an
    # updated version of content that a course could pull in. But more recently,
    # we've decided to do those version references at the level of the
    # individual blocks being used, since a Learning Core backed library is
    # intended to be referenced in multiple course locations and not 1:1 like v1
    # libraries. The top level version stays for now because LegacyLibraryContentBlock
    # uses it, but that should hopefully change before the Redwood release.
    version = 0 if last_publish_log is None else last_publish_log.pk
    published_by = ""
    if last_publish_log and last_publish_log.published_by:
        published_by = last_publish_log.published_by.username

    return ContentLibraryMetadata(
        key=library_key,
        title=learning_package.title,
        description=learning_package.description,
        num_blocks=num_blocks,
        version=version,
        last_published=None if last_publish_log is None else last_publish_log.published_at,
        published_by=published_by,
        last_draft_created=last_draft_created,
        last_draft_created_by=last_draft_created_by,
        allow_lti=ref.allow_lti,
        allow_public_learning=ref.allow_public_learning,
        allow_public_read=ref.allow_public_read,
        has_unpublished_changes=has_unpublished_changes,
        has_unpublished_deletes=has_unpublished_deletes,
        license=ref.license,
        created=learning_package.created,
        updated=learning_package.updated,
        learning_package_id=learning_package.pk,
    )


def create_library(
    org: str,
    slug: str,
    title: str,
    description: str = "",
    allow_public_learning: bool = False,
    allow_public_read: bool = False,
    library_license: str = ALL_RIGHTS_RESERVED,
) -> ContentLibraryMetadata:
    """
    Create a new content library.

    org: an organizations.models.Organization instance

    slug: a slug for this library like 'physics-problems'

    title: title for this library

    description: description of this library

    allow_public_learning: Allow anyone to read/learn from blocks in the LMS

    allow_public_read: Allow anyone to view blocks (including source) in Studio?

    Returns a ContentLibraryMetadata instance.
    """
    assert isinstance(org, Organization)
    validate_unicode_slug(slug)
    try:
        with transaction.atomic():
            ref = ContentLibrary.objects.create(
                org=org,
                slug=slug,
                allow_public_learning=allow_public_learning,
                allow_public_read=allow_public_read,
                license=library_license,
            )
            learning_package = authoring_api.create_learning_package(
                key=str(ref.library_key),
                title=title,
                description=description,
            )
            ref.learning_package = learning_package
            ref.save()

    except IntegrityError:
        raise LibraryAlreadyExists(slug)  # lint-amnesty, pylint: disable=raise-missing-from

    CONTENT_LIBRARY_CREATED.send_event(
        content_library=ContentLibraryData(
            library_key=ref.library_key
        )
    )
    return ContentLibraryMetadata(
        key=ref.library_key,
        title=title,
        description=description,
        num_blocks=0,
        version=0,
        last_published=None,
        allow_public_learning=ref.allow_public_learning,
        allow_public_read=ref.allow_public_read,
        license=library_license,
        learning_package_id=ref.learning_package.pk,
    )


def get_library_team(library_key: LibraryLocatorV2) -> list[ContentLibraryPermissionEntry]:
    """
    Get the list of users/groups granted permission to use this library.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    return [
        ContentLibraryPermissionEntry(user=entry.user, group=entry.group, access_level=entry.access_level)
        for entry in ref.permission_grants.all()
    ]


def get_library_user_permissions(library_key: LibraryLocatorV2, user: UserType) -> ContentLibraryPermissionEntry | None:
    """
    Fetch the specified user's access information. Will return None if no
    permissions have been granted.
    """
    if isinstance(user, AnonymousUser):
        return None  # Mostly here for the type checker
    ref = ContentLibrary.objects.get_by_key(library_key)
    grant = ref.permission_grants.filter(user=user).first()
    if grant is None:
        return None
    return ContentLibraryPermissionEntry(
        user=grant.user,
        group=grant.group,
        access_level=grant.access_level,
    )


def set_library_user_permissions(library_key: LibraryLocatorV2, user: UserType, access_level: str | None):
    """
    Change the specified user's level of access to this library.

    access_level should be one of the AccessLevel values defined above.
    """
    if isinstance(user, AnonymousUser):
        raise TypeError("Invalid user type")  # Mostly here for the type checker
    ref = ContentLibrary.objects.get_by_key(library_key)
    current_grant = get_library_user_permissions(library_key, user)
    if current_grant and current_grant.access_level == AccessLevel.ADMIN_LEVEL:
        if not ref.permission_grants.filter(access_level=AccessLevel.ADMIN_LEVEL).exclude(user_id=user.id).exists():
            raise LibraryPermissionIntegrityError(_('Cannot change or remove the access level for the only admin.'))

    if access_level is None:
        ref.permission_grants.filter(user=user).delete()
    else:
        ContentLibraryPermission.objects.update_or_create(
            library=ref,
            user=user,
            defaults={"access_level": access_level},
        )


def set_library_group_permissions(library_key: LibraryLocatorV2, group, access_level: str):
    """
    Change the specified group's level of access to this library.

    access_level should be one of the AccessLevel values defined above.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)

    if access_level is None:
        ref.permission_grants.filter(group=group).delete()
    else:
        ContentLibraryPermission.objects.update_or_create(
            library=ref,
            group=group,
            defaults={"access_level": access_level},
        )


def update_library(
    library_key: LibraryLocatorV2,
    title=None,
    description=None,
    allow_public_learning=None,
    allow_public_read=None,
    library_license=None,
):
    """
    Update a library's metadata
    (Slug cannot be changed as it would break IDs throughout the system.)

    A value of None means "don't change".
    """
    lib_obj_fields = [
        allow_public_learning, allow_public_read, library_license
    ]
    lib_obj_changed = any(field is not None for field in lib_obj_fields)
    learning_pkg_changed = any(field is not None for field in [title, description])

    # If nothing's changed, just return early.
    if (not lib_obj_changed) and (not learning_pkg_changed):
        return

    content_lib = ContentLibrary.objects.get_by_key(library_key)
    learning_package_id = content_lib.learning_package_id
    assert learning_package_id is not None

    with transaction.atomic():
        # We need to make updates to both the ContentLibrary and its linked
        # LearningPackage.
        if lib_obj_changed:
            if allow_public_learning is not None:
                content_lib.allow_public_learning = allow_public_learning
            if allow_public_read is not None:
                content_lib.allow_public_read = allow_public_read
            if library_license is not None:
                content_lib.license = library_license
            content_lib.save()

        if learning_pkg_changed:
            authoring_api.update_learning_package(
                learning_package_id,
                title=title,
                description=description,
            )

    CONTENT_LIBRARY_UPDATED.send_event(
        content_library=ContentLibraryData(
            library_key=content_lib.library_key
        )
    )

    return content_lib


def delete_library(library_key: LibraryLocatorV2) -> None:
    """
    Delete a content library
    """
    with transaction.atomic():
        content_lib = ContentLibrary.objects.get_by_key(library_key)
        learning_package = content_lib.learning_package
        content_lib.delete()

        # TODO: Move the LearningPackage delete() operation to an API call
        # TODO: We should eventually detach the LearningPackage and delete it
        #       asynchronously, especially if we need to delete a bunch of stuff
        #       on the filesystem for it.
        if learning_package:
            learning_package.delete()

    CONTENT_LIBRARY_DELETED.send_event(
        content_library=ContentLibraryData(
            library_key=library_key
        )
    )


def library_component_usage_key(
    library_key: LibraryLocatorV2,
    component: Component,
) -> LibraryUsageLocatorV2:
    """
    Returns a LibraryUsageLocatorV2 for the given library + component.
    """
    return LibraryUsageLocatorV2(  # type: ignore[abstract]
        library_key,
        block_type=component.component_type.name,
        usage_id=component.local_key,
    )


def get_allowed_block_types(library_key: LibraryLocatorV2):  # pylint: disable=unused-argument
    """
    Get a list of XBlock types that can be added to the specified content
    library.
    """
    # This import breaks in the LMS so keep it here. The LMS doesn't generally
    # use content libraries APIs directly but some tests may want to use them to
    # create libraries and then test library learning or course-library integration.
    from cms.djangoapps.contentstore import helpers as studio_helpers
    block_types = sorted(name for name, class_ in XBlock.load_classes())

    # Get enabled block types
    #
    # TODO: For now we are using `settings.LIBRARY_ENABLED_BLOCKS` without filtering
    # to return the enabled block types for all libraries. In the future, filtering will be
    # done based on a custom configuration per library.
    enabled_block_types = [item for item in block_types if item in settings.LIBRARY_ENABLED_BLOCKS]

    info = []
    for block_type in enabled_block_types:
        # TODO: unify the contentstore helper with the xblock.api version of
        # xblock_type_display_name
        display_name = studio_helpers.xblock_type_display_name(block_type, None)
        # For now as a crude heuristic, we exclude blocks that don't have a display_name
        if display_name:
            info.append(LibraryXBlockType(block_type=block_type, display_name=display_name))
    return info


def publish_changes(library_key: LibraryLocatorV2, user_id: int | None = None):
    """
    Publish all pending changes to the specified library.
    """
    learning_package = ContentLibrary.objects.get_by_key(library_key).learning_package
    assert learning_package is not None  # shouldn't happen but it's technically possible.
    authoring_api.publish_all_drafts(learning_package.id, published_by=user_id)

    CONTENT_LIBRARY_UPDATED.send_event(
        content_library=ContentLibraryData(
            library_key=library_key,
            update_blocks=True
        )
    )


def revert_changes(library_key: LibraryLocatorV2, user_id: int | None = None) -> None:
    """
    Revert all pending changes to the specified library, restoring it to the
    last published version.
    """
    learning_package = ContentLibrary.objects.get_by_key(library_key).learning_package
    assert learning_package is not None  # shouldn't happen but it's technically possible.
    authoring_api.reset_drafts_to_published(learning_package.id, reset_by=user_id)

    CONTENT_LIBRARY_UPDATED.send_event(
        content_library=ContentLibraryData(
            library_key=library_key,
            update_blocks=True
        )
    )

    # For each collection, trigger LIBRARY_COLLECTION_UPDATED signal and set background=True to trigger
    # collection indexing asynchronously.
    #
    # This is to update component counts in all library collections,
    # because there may be components that have been discarded in the revert.
    for collection in authoring_api.get_collections(learning_package.id):
        LIBRARY_COLLECTION_UPDATED.send_event(
            library_collection=LibraryCollectionData(
                collection_key=library_collection_locator(
                    library_key=library_key,
                    collection_key=collection.key,
                ),
                background=True,
            )
        )

    # Reindex components that are in collections
    #
    # Use case: When a component that was within a collection has been deleted
    # and the changes are reverted, the component should appear in the
    # collection again.
    components_in_collections = authoring_api.get_components(
        learning_package.id, draft=True, namespace='xblock.v1',
    ).filter(publishable_entity__collections__isnull=False)

    for component in components_in_collections:
        usage_key = library_component_usage_key(library_key, component)

        CONTENT_OBJECT_ASSOCIATIONS_CHANGED.send_event(
            content_object=ContentObjectChangedData(
                object_id=str(usage_key),
                changes=["collections"],
            ),
        )
