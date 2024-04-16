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

Import from Courseware
----------------------

Content Libraries can import blocks from Courseware (Modulestore).  The import
can be done per-course, by listing its content, and supports both access to
remote platform instances as well as local modulestore APIs.  Additionally,
there are Celery-based interfaces suitable for background processing controlled
through RESTful APIs (see :mod:`.views`).
"""
from __future__ import annotations

import abc
import collections
from datetime import datetime, timezone
import base64
import hashlib
import logging

import attr
import requests

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.validators import validate_unicode_slug
from django.db import IntegrityError, transaction
from django.db.models import Q, QuerySet
from django.utils.translation import gettext as _
from edx_rest_api_client.client import OAuthAPIClient
from lxml import etree
from opaque_keys.edx.keys import UsageKey, UsageKeyV2
from opaque_keys.edx.locator import (
    LibraryLocatorV2,
    LibraryUsageLocatorV2,
    LibraryLocator as LibraryLocatorV1
)
from opaque_keys import InvalidKeyError
from openedx_events.content_authoring.data import ContentLibraryData, LibraryBlockData
from openedx_events.content_authoring.signals import (
    CONTENT_LIBRARY_CREATED,
    CONTENT_LIBRARY_DELETED,
    CONTENT_LIBRARY_UPDATED,
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_DELETED,
    LIBRARY_BLOCK_UPDATED,
)
from openedx_learning.core.publishing import api as publishing_api
from openedx_learning.core.contents import api as contents_api
from openedx_learning.core.components import api as components_api
from openedx_learning.core.components.models import Component
from organizations.models import Organization
from xblock.core import XBlock
from xblock.exceptions import XBlockNotFoundError

from openedx.core.djangoapps.xblock.api import get_component_from_usage_key, xblock_type_display_name
from openedx.core.lib.xblock_serializer.api import serialize_modulestore_block_for_blockstore
from xmodule.library_root_xblock import LibraryRoot as LibraryRootV1
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from . import permissions, tasks
from .constants import ALL_RIGHTS_RESERVED, COMPLEX
from .models import ContentLibrary, ContentLibraryPermission, ContentLibraryBlockImportTask

log = logging.getLogger(__name__)


# Exceptions
# ==========


ContentLibraryNotFound = ContentLibrary.DoesNotExist


class ContentLibraryBlockNotFound(XBlockNotFoundError):
    """ XBlock not found in the content library """


class LibraryAlreadyExists(KeyError):
    """ A library with the specified slug already exists """


class LibraryBlockAlreadyExists(KeyError):
    """ An XBlock with that ID already exists in the library """


class BlockLimitReachedError(Exception):
    """ Maximum number of allowed XBlocks in the library reached """


class IncompatibleTypesError(Exception):
    """ Library type constraint violated """


class InvalidNameError(ValueError):
    """ The specified name/identifier is not valid """


class LibraryPermissionIntegrityError(IntegrityError):
    """ Thrown when an operation would cause insane permissions. """


# Models
# ======


@attr.s
class ContentLibraryMetadata:
    """
    Class that represents the metadata about a content library.
    """
    key = attr.ib(type=LibraryLocatorV2)
    title = attr.ib("")
    description = attr.ib("")
    num_blocks = attr.ib(0)
    version = attr.ib(0)
    type = attr.ib(default=COMPLEX)
    last_published = attr.ib(default=None, type=datetime)
    has_unpublished_changes = attr.ib(False)
    # has_unpublished_deletes will be true when the draft version of the library's bundle
    # contains deletes of any XBlocks that were in the most recently published version
    has_unpublished_deletes = attr.ib(False)
    allow_lti = attr.ib(False)
    # Allow any user (even unregistered users) to view and interact directly
    # with this library's content in the LMS
    allow_public_learning = attr.ib(False)
    # Allow any user with Studio access to view this library's content in
    # Studio, use it in their courses, and copy content out of this library.
    allow_public_read = attr.ib(False)
    license = attr.ib("")


class AccessLevel:
    """ Enum defining library access levels/permissions """
    ADMIN_LEVEL = ContentLibraryPermission.ADMIN_LEVEL
    AUTHOR_LEVEL = ContentLibraryPermission.AUTHOR_LEVEL
    READ_LEVEL = ContentLibraryPermission.READ_LEVEL
    NO_ACCESS = None


@attr.s
class ContentLibraryPermissionEntry:
    """
    A user or group granted permission to use a content library.
    """
    user = attr.ib(type=AbstractUser, default=None)
    group = attr.ib(type=Group, default=None)
    access_level = attr.ib(AccessLevel.NO_ACCESS)


@attr.s
class LibraryXBlockMetadata:
    """
    Class that represents the metadata about an XBlock in a content library.
    """
    usage_key = attr.ib(type=LibraryUsageLocatorV2)
    display_name = attr.ib("")
    has_unpublished_changes = attr.ib(False)
    tags_count = attr.ib(0)

    @classmethod
    def from_component(cls, library_key, component):
        """
        Construct a LibraryXBlockMetadata from a Component object.
        """
        return cls(
            usage_key=LibraryUsageLocatorV2(
                library_key,
                component.component_type.name,
                component.local_key,
            ),
            display_name=component.versioning.draft.title,
            has_unpublished_changes=component.versioning.has_unpublished_changes
        )


@attr.s
class LibraryXBlockStaticFile:
    """
    Class that represents a static file in a content library, associated with
    a particular XBlock.
    """
    # File path e.g. "diagram.png"
    # In some rare cases it might contain a folder part, e.g. "en/track1.srt"
    path = attr.ib("")
    # Publicly accessible URL where the file can be downloaded
    url = attr.ib("")
    # Size in bytes
    size = attr.ib(0)


@attr.s
class LibraryXBlockType:
    """
    An XBlock type that can be added to a content library
    """
    block_type = attr.ib("")
    display_name = attr.ib("")


# General APIs
# ============


def get_libraries_for_user(user, org=None, library_type=None, text_search=None):
    """
    Return content libraries that the user has permission to view.
    """
    filter_kwargs = {}
    if org:
        filter_kwargs['org__short_name'] = org
    if library_type:
        filter_kwargs['type'] = library_type
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

    return permissions.perms[permissions.CAN_VIEW_THIS_CONTENT_LIBRARY].filter(user, qs)


def get_metadata(queryset, text_search=None):
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
            type=lib.type,
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
        )
        for lib in queryset
    ]
    return libraries


def require_permission_for_library_key(library_key, user, permission):
    """
    Given any of the content library permission strings defined in
    openedx.core.djangoapps.content_libraries.permissions,
    check if the given user has that permission for the library with the
    specified library ID.

    Raises django.core.exceptions.PermissionDenied if the user doesn't have
    permission.
    """
    library_obj = ContentLibrary.objects.get_by_key(library_key)
    if not user.has_perm(permission, obj=library_obj):
        raise PermissionDenied


def get_library(library_key):
    """
    Get the library with the specified key. Does not check permissions.
    returns a ContentLibraryMetadata instance.

    Raises ContentLibraryNotFound if the library doesn't exist.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    learning_package = ref.learning_package
    num_blocks = publishing_api.get_all_drafts(learning_package.id).count()
    last_publish_log = publishing_api.get_last_publish(learning_package.id)
    has_unpublished_changes = publishing_api.get_entities_with_unpublished_changes(learning_package.id) \
                                            .exists()

    # TODO: I'm doing this one to match already-existing behavior, but this is
    # something that we should remove. It exists to accomodate some complexities
    # with how Blockstore staged changes, but Learning Core works differently,
    # and has_unpublished_changes should be sufficient.
    has_unpublished_deletes = publishing_api.get_entities_with_unpublished_deletes(learning_package.id) \
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
    # intended to be used for many LibraryContentBlocks and not 1:1 like v1
    # libraries. The top level version stays for now because LibraryContentBlock
    # uses it, but that should hopefully change before the Redwood release.
    version = 0 if last_publish_log is None else last_publish_log.pk

    return ContentLibraryMetadata(
        key=library_key,
        title=learning_package.title,
        type=ref.type,
        description=ref.learning_package.description,
        num_blocks=num_blocks,
        version=version,
        last_published=None if last_publish_log is None else last_publish_log.published_at,
        allow_lti=ref.allow_lti,
        allow_public_learning=ref.allow_public_learning,
        allow_public_read=ref.allow_public_read,
        has_unpublished_changes=has_unpublished_changes,
        has_unpublished_deletes=has_unpublished_deletes,
        license=ref.license,
    )


def create_library(
        org,
        slug,
        title,
        description="",
        allow_public_learning=False,
        allow_public_read=False,
        library_license=ALL_RIGHTS_RESERVED,
        library_type=COMPLEX,
):
    """
    Create a new content library.

    org: an organizations.models.Organization instance

    slug: a slug for this library like 'physics-problems'

    title: title for this library

    description: description of this library

    allow_public_learning: Allow anyone to read/learn from blocks in the LMS

    allow_public_read: Allow anyone to view blocks (including source) in Studio?

    library_type: Deprecated parameter, not really used. Set to COMPLEX.

    Returns a ContentLibraryMetadata instance.
    """
    assert isinstance(org, Organization)
    validate_unicode_slug(slug)
    try:
        with transaction.atomic():
            ref = ContentLibrary.objects.create(
                org=org,
                slug=slug,
                type=library_type,
                allow_public_learning=allow_public_learning,
                allow_public_read=allow_public_read,
                license=library_license,
            )
            learning_package = publishing_api.create_learning_package(
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
        type=library_type,
        description=description,
        num_blocks=0,
        version=0,
        last_published=None,
        allow_public_learning=ref.allow_public_learning,
        allow_public_read=ref.allow_public_read,
        license=library_license,
    )


def get_library_team(library_key):
    """
    Get the list of users/groups granted permission to use this library.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    return [
        ContentLibraryPermissionEntry(user=entry.user, group=entry.group, access_level=entry.access_level)
        for entry in ref.permission_grants.all()
    ]


def get_library_user_permissions(library_key, user):
    """
    Fetch the specified user's access information. Will return None if no
    permissions have been granted.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    grant = ref.permission_grants.filter(user=user).first()
    if grant is None:
        return None
    return ContentLibraryPermissionEntry(
        user=grant.user,
        group=grant.group,
        access_level=grant.access_level,
    )


def set_library_user_permissions(library_key, user, access_level):
    """
    Change the specified user's level of access to this library.

    access_level should be one of the AccessLevel values defined above.
    """
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


def set_library_group_permissions(library_key, group, access_level):
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
        library_key,
        title=None,
        description=None,
        allow_public_learning=None,
        allow_public_read=None,
        library_type=None,
        library_license=None,
):
    """
    Update a library's metadata
    (Slug cannot be changed as it would break IDs throughout the system.)

    A value of None means "don't change".
    """
    lib_obj_fields = [
        allow_public_learning, allow_public_read, library_type, library_license
    ]
    lib_obj_changed = any(field is not None for field in lib_obj_fields)
    learning_pkg_changed = any(field is not None for field in [title, description])

    # If nothing's changed, just return early.
    if (not lib_obj_changed) and (not learning_pkg_changed):
        return

    content_lib = ContentLibrary.objects.get_by_key(library_key)

    with transaction.atomic():
        # We need to make updates to both the ContentLibrary and its linked
        # LearningPackage.
        if lib_obj_changed:
            if allow_public_learning is not None:
                content_lib.allow_public_learning = allow_public_learning
            if allow_public_read is not None:
                content_lib.allow_public_read = allow_public_read
            if library_type is not None:
                # TODO: Get rid of this field entirely, and remove library_type
                # from any functions that take it as an argument.
                content_lib.library_type = library_type
            if library_license is not None:
                content_lib.library_license = library_license
            content_lib.save()

        if learning_pkg_changed:
            publishing_api.update_learning_package(
                content_lib.learning_package_id,
                title=title,
                description=description,
            )

    CONTENT_LIBRARY_UPDATED.send_event(
        content_library=ContentLibraryData(
            library_key=content_lib.library_key
        )
    )

    return content_lib


def delete_library(library_key):
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
        learning_package.delete()

    CONTENT_LIBRARY_DELETED.send_event(
        content_library=ContentLibraryData(
            library_key=library_key
        )
    )


def _get_library_component_tags_count(library_key) -> dict:
    """
    Get the count of tags that are applied to each component in this library, as a dict.
    """
    # Import content_tagging.api here to avoid circular imports
    from openedx.core.djangoapps.content_tagging.api import get_object_tag_counts

    # Create a pattern to match the IDs of the library components, e.g. "lb:org:id*"
    library_key_pattern = str(library_key).replace("lib:", "lb:", 1) + "*"
    return get_object_tag_counts(library_key_pattern, count_implicit=True)


def get_library_components(library_key, text_search=None, block_types=None) -> QuerySet[Component]:
    """
    Get the library components and filter.

    TODO: Full text search needs to be implemented as a custom lookup for MySQL,
    but it should have a fallback to still work in SQLite.
    """
    lib = ContentLibrary.objects.get_by_key(library_key)  # type: ignore[attr-defined]
    learning_package = lib.learning_package
    components = components_api.get_components(
        learning_package.id,
        draft=True,
        namespace='xblock.v1',
        type_names=block_types,
        draft_title=text_search,
    )
    return components


def get_library_block(usage_key) -> LibraryXBlockMetadata:
    """
    Get metadata about (the draft version of) one specific XBlock in a library.

    This will raise ContentLibraryBlockNotFound if there is no draft version of
    this block (i.e. it's been soft-deleted from Studio), even if there is a
    live published version of it in the LMS.
    """
    try:
        component = get_component_from_usage_key(usage_key)
    except ObjectDoesNotExist as exc:
        raise ContentLibraryBlockNotFound(usage_key) from exc

    # The component might have existed at one point, but no longer does because
    # the draft was soft-deleted. This is actually a weird edge case and I'm not
    # clear on what the proper behavior should be, since (a) the published
    # version still exists; and (b) we might want to make some queries on the
    # block even after it's been removed, since there might be versioned
    # references to it.
    draft_version = component.versioning.draft
    if not draft_version:
        raise ContentLibraryBlockNotFound(usage_key)

    published_version = component.versioning.published

    return LibraryXBlockMetadata(
        usage_key=usage_key,
        display_name=draft_version.title,
        has_unpublished_changes=(draft_version != published_version),
    )


def set_library_block_olx(usage_key, new_olx_str):
    """
    Replace the OLX source of the given XBlock.

    This is only meant for use by developers or API client applications, as
    very little validation is done and this can easily result in a broken XBlock
    that won't load.
    """
    # because this old pylint can't understand attr.ib() objects, pylint: disable=no-member
    assert isinstance(usage_key, LibraryUsageLocatorV2)

    # Make sure the block exists:
    _block_metadata = get_library_block(usage_key)

    # Verify that the OLX parses, at least as generic XML, and the root tag is correct:
    node = etree.fromstring(new_olx_str)
    if node.tag != usage_key.block_type:
        raise ValueError(
            f"Tried to set the OLX of a {usage_key.block_type} block to a <{node.tag}> node. "
            f"{usage_key=!s}, {new_olx_str=}"
        )

    # We're intentionally NOT checking if the XBlock type is installed, since
    # this is one of the only tools you can reach for to edit content for an
    # XBlock that's broken or missing.
    component = get_component_from_usage_key(usage_key)

    # Get the title from the new OLX (or default to the default specified on the
    # XBlock's display_name field.
    new_title = node.attrib.get(
        "display_name",
        xblock_type_display_name(usage_key.block_type),
    )

    now = datetime.now(tz=timezone.utc)

    with transaction.atomic():
        new_content = contents_api.get_or_create_text_content(
            component.learning_package_id,
            get_or_create_olx_media_type(usage_key.block_type).id,
            text=new_olx_str,
            created=now,
        )
        components_api.create_next_version(
            component.pk,
            title=new_title,
            content_to_replace={
                'block.xml': new_content.pk,
            },
            created=now,
        )

    LIBRARY_BLOCK_UPDATED.send_event(
        library_block=LibraryBlockData(
            library_key=usage_key.context_key,
            usage_key=usage_key
        )
    )


def create_library_block(library_key, block_type, definition_id):
    """
    Create a new XBlock in this library of the specified type (e.g. "html").
    """
    # It's in the serializer as ``definition_id``, but for our purposes, it's
    # the block_id. See the comments in ``LibraryXBlockCreationSerializer`` for
    # more details. TODO: Change the param name once we change the serializer.
    block_id = definition_id

    assert isinstance(library_key, LibraryLocatorV2)
    ref = ContentLibrary.objects.get_by_key(library_key)
    if ref.type != COMPLEX:
        if block_type != ref.type:
            raise IncompatibleTypesError(
                _('Block type "{block_type}" is not compatible with library type "{library_type}".').format(
                    block_type=block_type, library_type=ref.type,
                )
            )

    # If adding a component would take us over our max, return an error.
    component_count = publishing_api.get_all_drafts(ref.learning_package.id).count()
    if component_count + 1 > settings.MAX_BLOCKS_PER_CONTENT_LIBRARY:
        raise BlockLimitReachedError(
            _("Library cannot have more than {} Components").format(
                settings.MAX_BLOCKS_PER_CONTENT_LIBRARY
            )
        )

    # Make sure the proposed ID will be valid:
    validate_unicode_slug(block_id)
    # Ensure the XBlock type is valid and installed:
    XBlock.load_class(block_type)  # Will raise an exception if invalid
    # Make sure the new ID is not taken already:
    usage_key = LibraryUsageLocatorV2(
        lib_key=library_key,
        block_type=block_type,
        usage_id=block_id,
    )

    if _component_exists(usage_key):
        raise LibraryBlockAlreadyExists(f"An XBlock with ID '{usage_key}' already exists")

    _create_component_for_block(ref, usage_key)

    # Now return the metadata about the new block:
    LIBRARY_BLOCK_CREATED.send_event(
        library_block=LibraryBlockData(
            library_key=ref.library_key,
            usage_key=usage_key
        )
    )

    return get_library_block(usage_key)


def _component_exists(usage_key: UsageKeyV2) -> bool:
    """
    Does a Component exist for this usage key?

    This is a lower-level function that will return True if a Component object
    exists, even if it was soft-deleted, and there is no active draft version.
    """
    try:
        get_component_from_usage_key(usage_key)
    except ObjectDoesNotExist:
        return False
    return True


def get_or_create_olx_media_type(block_type: str) -> contents_api.MediaType:
    """
    Get or create a MediaType for the block type.

    Learning Core stores all Content with a Media Type (a.k.a. MIME type). For
    OLX, we use the "application/vnd.*" convention, per RFC 6838.
    """
    return contents_api.get_or_create_media_type(
        f"application/vnd.openedx.xblock.v1.{block_type}+xml"
    )


def _create_component_for_block(content_lib, usage_key):
    """
    Create a Component for an XBlock type, and initialize it.

    This will create a Component, along with its first ComponentVersion. The tag
    in the OLX will have no attributes, e.g. `<problem />`. This first version
    will be set as the current draft. This function does not publish the
    Component.

    TODO: We should probably shift this to openedx.core.djangoapps.xblock.api
    (along with its caller) since it gives runtime storage specifics. The
    Library-specific logic stays in this module, so "create a block for my lib"
    should stay here, but "making a block means creating a component with
    text data like X" goes in xblock.api.
    """
    display_name = xblock_type_display_name(usage_key.block_type)
    now = datetime.now(tz=timezone.utc)
    xml_text = f'<{usage_key.block_type} />'

    learning_package = content_lib.learning_package

    with transaction.atomic():
        component_type = components_api.get_or_create_component_type(
            "xblock.v1", usage_key.block_type
        )
        component, component_version = components_api.create_component_and_version(
            learning_package.id,
            component_type=component_type,
            local_key=usage_key.block_id,
            title=display_name,
            created=now,
            created_by=None,
        )
        content = contents_api.get_or_create_text_content(
            learning_package.id,
            get_or_create_olx_media_type(usage_key.block_type).id,
            text=xml_text,
            created=now,
        )
        components_api.create_component_version_content(
            component_version.pk,
            content.id,
            key="block.xml",
            learner_downloadable=False
        )


def delete_library_block(usage_key, remove_from_parent=True):
    """
    Delete the specified block from this library (soft delete).
    """
    component = get_component_from_usage_key(usage_key)
    publishing_api.soft_delete_draft(component.pk)

    LIBRARY_BLOCK_DELETED.send_event(
        library_block=LibraryBlockData(
            library_key=usage_key.context_key,
            usage_key=usage_key
        )
    )


def get_library_block_static_asset_files(usage_key) -> list[LibraryXBlockStaticFile]:
    """
    Given an XBlock in a content library, list all the static asset files
    associated with that XBlock.

    Returns a list of LibraryXBlockStaticFile objects, sorted by path.

    TODO: This is not yet implemented for Learning Core backed libraries.
    TODO: Should this be in the general XBlock API rather than the libraries API?
    """
    return []


def add_library_block_static_asset_file(usage_key, file_name, file_content) -> LibraryXBlockStaticFile:
    """
    Upload a static asset file into the library, to be associated with the
    specified XBlock. Will silently overwrite an existing file of the same name.

    file_name should be a name like "doc.pdf". It may optionally contain slashes
        like 'en/doc.pdf'
    file_content should be a binary string.

    Returns a LibraryXBlockStaticFile object.

    Sends a LIBRARY_BLOCK_UPDATED event.

    Example:
        video_block = UsageKey.from_string("lb:VideoTeam:python-intro:video:1")
        add_library_block_static_asset_file(video_block, "subtitles-en.srt", subtitles.encode('utf-8'))
    """
    raise NotImplementedError("Static assets not yet implemented for Learning Core")


def delete_library_block_static_asset_file(usage_key, file_name):
    """
    Delete a static asset file from the library.

    Sends a LIBRARY_BLOCK_UPDATED event.

    Example:
        video_block = UsageKey.from_string("lb:VideoTeam:python-intro:video:1")
        delete_library_block_static_asset_file(video_block, "subtitles-en.srt")
    """
    raise NotImplementedError("Static assets not yet implemented for Learning Core")


def get_allowed_block_types(library_key):  # pylint: disable=unused-argument
    """
    Get a list of XBlock types that can be added to the specified content
    library.
    """
    # This import breaks in the LMS so keep it here. The LMS doesn't generally
    # use content libraries APIs directly but some tests may want to use them to
    # create libraries and then test library learning or course-library integration.
    from cms.djangoapps.contentstore import helpers as studio_helpers
    # TODO: return support status and template options
    # See cms/djangoapps/contentstore/views/component.py
    block_types = sorted(name for name, class_ in XBlock.load_classes())
    lib = get_library(library_key)
    if lib.type != COMPLEX:
        # Problem and Video libraries only permit XBlocks of the same name.
        block_types = (name for name in block_types if name == lib.type)
    info = []
    for block_type in block_types:
        # TODO: unify the contentstore helper with the xblock.api version of
        # xblock_type_display_name
        display_name = studio_helpers.xblock_type_display_name(block_type, None)
        # For now as a crude heuristic, we exclude blocks that don't have a display_name
        if display_name:
            info.append(LibraryXBlockType(block_type=block_type, display_name=display_name))
    return info


def publish_changes(library_key):
    """
    Publish all pending changes to the specified library.
    """
    learning_package = ContentLibrary.objects.get_by_key(library_key).learning_package

    publishing_api.publish_all_drafts(learning_package.id)

    CONTENT_LIBRARY_UPDATED.send_event(
        content_library=ContentLibraryData(
            library_key=library_key,
            update_blocks=True
        )
    )


def revert_changes(library_key):
    """
    Revert all pending changes to the specified library, restoring it to the
    last published version.
    """
    learning_package = ContentLibrary.objects.get_by_key(library_key).learning_package
    publishing_api.reset_drafts_to_published(learning_package.id)

    CONTENT_LIBRARY_UPDATED.send_event(
        content_library=ContentLibraryData(
            library_key=library_key,
            update_blocks=True
        )
    )


# V1/V2 Compatibility Helpers
# (Should be removed as part of
#  https://github.com/openedx/edx-platform/issues/32457)
# ======================================================

def get_v1_or_v2_library(
    library_id: str | LibraryLocatorV1 | LibraryLocatorV2,
    version: str | int | None,
) -> LibraryRootV1 | ContentLibraryMetadata | None:
    """
    Fetch either a V1 or V2 content library from a V1/V2 key (or key string) and version.

    V1 library versions are Mongo ObjectID strings.
    V2 library versions can be positive ints, or strings of positive ints.
    Passing version=None will return the latest version the library.

    Returns None if not found.
    If key is invalid, raises InvalidKeyError.
    For V1, if key has a version, it is ignored in favor of `version`.
    For V2, if version is provided but it isn't an int or parseable to one, we raise a ValueError.

    Examples:
    * get_v1_or_v2_library("library-v1:ProblemX+PR0B", None)       -> <LibraryRootV1>
    * get_v1_or_v2_library("library-v1:ProblemX+PR0B", "65ff...")  -> <LibraryRootV1>
    * get_v1_or_v2_library("lib:RG:rg-1", None)                    -> <ContentLibraryMetadata>
    * get_v1_or_v2_library("lib:RG:rg-1", "36")                    -> <ContentLibraryMetadata>
    * get_v1_or_v2_library("lib:RG:rg-1", "xyz")                   -> <ValueError>
    * get_v1_or_v2_library("notakey", "xyz")                       -> <InvalidKeyError>

    If you just want to get a V2 library, use `get_library` instead.
    """
    library_key: LibraryLocatorV1 | LibraryLocatorV2
    if isinstance(library_id, str):
        try:
            library_key = LibraryLocatorV1.from_string(library_id)
        except InvalidKeyError:
            library_key = LibraryLocatorV2.from_string(library_id)
    else:
        library_key = library_id
    if isinstance(library_key, LibraryLocatorV2):
        v2_version: int | None
        if version:
            v2_version = int(version)
        else:
            v2_version = None
        try:
            library = get_library(library_key)
            if v2_version is not None and library.version != v2_version:
                raise NotImplementedError(
                    f"Tried to load version {v2_version} of blockstore-based library {library_key}. "
                    f"Currently, only the latest version ({library.version}) may be loaded. "
                    "This is a known issue. "
                    "It will be fixed before the production release of blockstore-based (V2) content libraries. "
                )
            return library
        except ContentLibrary.DoesNotExist:
            return None
    elif isinstance(library_key, LibraryLocatorV1):
        v1_version: str | None
        if version:
            v1_version = str(version)
        else:
            v1_version = None
        store = modulestore()
        library_key = library_key.for_branch(ModuleStoreEnum.BranchName.library).for_version(v1_version)
        try:
            return store.get_library(library_key, remove_version=False, remove_branch=False, head_validation=False)
        except ItemNotFoundError:
            return None


# Import from Courseware
# ======================


class BaseEdxImportClient(abc.ABC):
    """
    Base class for all courseware import clients.

    Import clients are wrappers tailored to implement the steps used in the
    import APIs and can leverage different backends.  It is not aimed towards
    being a generic API client for Open edX.
    """

    EXPORTABLE_BLOCK_TYPES = {
        "drag-and-drop-v2",
        "problem",
        "html",
        "video",
    }

    def __init__(self, library_key=None, library=None, use_course_key_as_block_id_suffix=True):
        """
        Initialize an import client for a library.

        The method accepts either a library object or a key to a library object.
        """
        self.use_course_key_as_block_id_suffix = use_course_key_as_block_id_suffix
        if bool(library_key) == bool(library):
            raise ValueError('Provide at least one of `library_key` or '
                             '`library`, but not both.')
        if library is None:
            library = ContentLibrary.objects.get_by_key(library_key)
        self.library = library

    @abc.abstractmethod
    def get_block_data(self, block_key):
        """
        Get the block's OLX and static files, if any.
        """

    @abc.abstractmethod
    def get_export_keys(self, course_key):
        """
        Get all exportable block keys of a given course.
        """

    @abc.abstractmethod
    def get_block_static_data(self, asset_file):
        """
        Get the contents of an asset_file..
        """

    def import_block(self, modulestore_key):
        """
        Import a single modulestore block.
        """
        block_data = self.get_block_data(modulestore_key)

        # Get or create the block in the library.
        #
        # To dedup blocks from different courses with the same ID, we hash the
        # course key into the imported block id.

        course_key_id = base64.b32encode(
            hashlib.blake2s(
                str(modulestore_key.course_key).encode()
            ).digest()
        )[:16].decode().lower()

        # add the course_key_id if use_course_key_as_suffix is enabled to increase the namespace.
        # The option exists to not use the course key as a suffix because
        # in order to preserve learner state in the v1 to v2 libraries migration,
        # the v2 and v1 libraries' child block ids must be the same.
        block_id = (
            # Prepend 'c' to allow changing hash without conflicts.
            f"{modulestore_key.block_id}_c{course_key_id}"
            if self.use_course_key_as_block_id_suffix
            else f"{modulestore_key.block_id}"
        )

        log.info('Importing to library block: id=%s', block_id)
        try:
            library_block = create_library_block(
                self.library.library_key,
                modulestore_key.block_type,
                block_id,
            )
            blockstore_key = library_block.usage_key
        except LibraryBlockAlreadyExists:
            blockstore_key = LibraryUsageLocatorV2(
                lib_key=self.library.library_key,
                block_type=modulestore_key.block_type,
                usage_id=block_id,
            )
            get_library_block(blockstore_key)
            log.warning('Library block already exists: Appending static files '
                        'and overwriting OLX: %s', str(blockstore_key))

        # Handle static files.

        files = [
            f.path for f in
            get_library_block_static_asset_files(blockstore_key)
        ]
        for filename, static_file in block_data.get('static_files', {}).items():
            if filename in files:
                # Files already added, move on.
                continue
            file_content = self.get_block_static_data(static_file)
            add_library_block_static_asset_file(
                blockstore_key, filename, file_content)
            files.append(filename)

        # Import OLX.

        set_library_block_olx(blockstore_key, block_data['olx'])

    def import_blocks_from_course(self, course_key, progress_callback):
        """
        Import all eligible blocks from course key.

        Progress is reported through ``progress_callback``, guaranteed to be
        called within an exception handler if ``exception is not None``.
        """

        # Query the course and rerieve all course blocks.

        export_keys = self.get_export_keys(course_key)
        if not export_keys:
            raise ValueError(f"The courseware course {course_key} does not have "
                             "any exportable content.  No action taken.")

        # Import each block, skipping the ones that fail.

        for index, block_key in enumerate(export_keys):
            try:
                log.info('Importing block: %s/%s: %s', index + 1, len(export_keys), block_key)
                self.import_block(block_key)
            except Exception as exc:  # pylint: disable=broad-except
                log.exception("Error importing block: %s", block_key)
                progress_callback(block_key, index + 1, len(export_keys), exc)
            else:
                log.info('Successfully imported: %s/%s: %s', index + 1, len(export_keys), block_key)
                progress_callback(block_key, index + 1, len(export_keys), None)

        log.info("Publishing library: %s", self.library.library_key)
        publish_changes(self.library.library_key)


class EdxModulestoreImportClient(BaseEdxImportClient):
    """
    An import client based on the local instance of modulestore.
    """

    def __init__(self, modulestore_instance=None, **kwargs):
        """
        Initialize the client with a modulestore instance.
        """
        super().__init__(**kwargs)
        self.modulestore = modulestore_instance or modulestore()

    def get_block_data(self, block_key):
        """
        Get block OLX by serializing it from modulestore directly.
        """
        block = self.modulestore.get_item(block_key)
        data = serialize_modulestore_block_for_blockstore(block)
        return {'olx': data.olx_str,
                'static_files': {s.name: s for s in data.static_files}}

    def get_export_keys(self, course_key):
        """
        Retrieve the course from modulestore and traverse its content tree.
        """
        course = self.modulestore.get_course(course_key)
        if isinstance(course_key, LibraryLocatorV1):
            course = self.modulestore.get_library(course_key)
        export_keys = set()
        blocks_q = collections.deque(course.get_children())
        while blocks_q:
            block = blocks_q.popleft()
            usage_id = block.scope_ids.usage_id
            if usage_id in export_keys:
                continue
            if usage_id.block_type in self.EXPORTABLE_BLOCK_TYPES:
                export_keys.add(usage_id)
            if block.has_children:
                blocks_q.extend(block.get_children())
        return list(export_keys)

    def get_block_static_data(self, asset_file):
        """
        Get static content from its URL if available, otherwise from its data.
        """
        if asset_file.data:
            return asset_file.data
        resp = requests.get(f"http://{settings.CMS_BASE}" + asset_file.url)
        resp.raise_for_status()
        return resp.content


class EdxApiImportClient(BaseEdxImportClient):
    """
    An import client based on a remote Open Edx API interface.

    TODO: Look over this class. We'll probably need to completely re-implement
    the import process.
    """

    URL_COURSES = "/api/courses/v1/courses/{course_key}"

    URL_MODULESTORE_BLOCK_OLX = "/api/olx-export/v1/xblock/{block_key}/"

    def __init__(self, lms_url, studio_url, oauth_key, oauth_secret, *args, **kwargs):
        """
        Initialize the API client with URLs and OAuth keys.
        """
        super().__init__(**kwargs)
        self.lms_url = lms_url
        self.studio_url = studio_url
        self.oauth_client = OAuthAPIClient(
            self.lms_url,
            oauth_key,
            oauth_secret,
        )

    def get_block_data(self, block_key):
        """
        See parent's docstring.
        """
        olx_path = self.URL_MODULESTORE_BLOCK_OLX.format(block_key=block_key)
        resp = self._get(self.studio_url + olx_path)
        return resp['blocks'][str(block_key)]

    def get_export_keys(self, course_key):
        """
        See parent's docstring.
        """
        course_blocks_url = self._get_course(course_key)['blocks_url']
        course_blocks = self._get(
            course_blocks_url,
            params={'all_blocks': True, 'depth': 'all'})['blocks']
        export_keys = []
        for block_info in course_blocks.values():
            if block_info['type'] in self.EXPORTABLE_BLOCK_TYPES:
                export_keys.append(UsageKey.from_string(block_info['id']))
        return export_keys

    def get_block_static_data(self, asset_file):
        """
        See parent's docstring.
        """
        if (asset_file['url'].startswith(self.studio_url)
                and 'export-file' in asset_file['url']):
            # We must call download this file with authentication. But
            # we only want to pass the auth headers if this is the same
            # studio instance, or else we could leak credentials to a
            # third party.
            path = asset_file['url'][len(self.studio_url):]
            resp = self._call('get', path)
        else:
            resp = requests.get(asset_file['url'])
            resp.raise_for_status()
        return resp.content

    def _get(self, *args, **kwargs):
        """
        Perform a get request to the client.
        """
        return self._json_call('get', *args, **kwargs)

    def _get_course(self, course_key):
        """
        Request details for a course.
        """
        course_url = self.lms_url + self.URL_COURSES.format(course_key=course_key)
        return self._get(course_url)

    def _json_call(self, method, *args, **kwargs):
        """
        Wrapper around request calls that ensures valid json responses.
        """
        return self._call(method, *args, **kwargs).json()

    def _call(self, method, *args, **kwargs):
        """
        Wrapper around request calls.
        """
        response = getattr(self.oauth_client, method)(*args, **kwargs)
        response.raise_for_status()
        return response


def import_blocks_create_task(library_key, course_key, use_course_key_as_block_id_suffix=True):
    """
    Create a new import block task.

    This API will schedule a celery task to perform the import, and it returns a
    import task object for polling.
    """
    library = ContentLibrary.objects.get_by_key(library_key)
    import_task = ContentLibraryBlockImportTask.objects.create(
        library=library,
        course_id=course_key,
    )
    result = tasks.import_blocks_from_course.apply_async(
        args=(import_task.pk, str(course_key), use_course_key_as_block_id_suffix)
    )
    log.info(f"Import block task created: import_task={import_task} "
             f"celery_task={result.id}")
    return import_task
