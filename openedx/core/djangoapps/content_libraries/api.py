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


import abc
import collections
from datetime import datetime
from uuid import UUID
import base64
import hashlib
import logging

import attr
import requests

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import PermissionDenied
from django.core.validators import validate_unicode_slug
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError
from lxml import etree
from opaque_keys.edx.keys import LearningContextKey, UsageKey
from opaque_keys.edx.locator import BundleDefinitionLocator, LibraryLocatorV2, LibraryUsageLocatorV2
from organizations.models import Organization
from xblock.core import XBlock
from xblock.exceptions import XBlockNotFoundError
from edx_rest_api_client.client import OAuthAPIClient
from openedx.core.djangoapps.content_libraries import permissions
from openedx.core.djangoapps.content_libraries.constants import DRAFT_NAME, COMPLEX
from openedx.core.djangoapps.content_libraries.library_bundle import LibraryBundle
from openedx.core.djangoapps.content_libraries.libraries_index import ContentLibraryIndexer, LibraryBlockIndexer
from openedx.core.djangoapps.content_libraries.models import (
    ContentLibrary,
    ContentLibraryPermission,
    ContentLibraryBlockImportTask,
)
from openedx.core.djangoapps.content_libraries.signals import (
    CONTENT_LIBRARY_CREATED,
    CONTENT_LIBRARY_UPDATED,
    CONTENT_LIBRARY_DELETED,
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_UPDATED,
    LIBRARY_BLOCK_DELETED,
)
from openedx.core.djangoapps.olx_rest_api.block_serializer import XBlockSerializer
from openedx.core.djangoapps.xblock.api import get_block_display_name, load_block
from openedx.core.djangoapps.xblock.learning_context.manager import get_learning_context_impl
from openedx.core.djangoapps.xblock.runtime.olx_parsing import XBlockInclude
from openedx.core.lib.blockstore_api import (
    get_bundle,
    get_bundles,
    get_bundle_file_data,
    get_bundle_files,
    get_or_create_bundle_draft,
    create_bundle,
    update_bundle,
    delete_bundle,
    write_draft_file,
    set_draft_link,
    commit_draft,
    delete_draft,
    BundleNotFound,
)
from openedx.core.djangolib import blockstore_cache
from openedx.core.djangolib.blockstore_cache import BundleCache
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

from . import tasks


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
    bundle_uuid = attr.ib(type=UUID)
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
    def_key = attr.ib(type=BundleDefinitionLocator)
    display_name = attr.ib("")
    has_unpublished_changes = attr.ib(False)


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


@attr.s
class LibraryBundleLink:
    """
    A link from a content library blockstore bundle to another blockstore bundle
    """
    # Bundle that is linked to
    bundle_uuid = attr.ib(type=UUID)
    # Link name (slug)
    id = attr.ib("")
    # What version of this bundle we are currently linking to.
    version = attr.ib(0)
    # What the latest version of the linked bundle is:
    # (if latest_version > version), the link can be "updated" to the latest version.
    latest_version = attr.ib(0)
    # Opaque key: If the linked bundle is a library or other learning context whose opaque key we can deduce, then this
    # is the key. If we don't know what type of blockstore bundle this link is pointing to, then this is blank.
    opaque_key = attr.ib(type=LearningContextKey, default=None)


class AccessLevel:  # lint-amnesty, pylint: disable=function-redefined
    """ Enum defining library access levels/permissions """
    ADMIN_LEVEL = ContentLibraryPermission.ADMIN_LEVEL
    AUTHOR_LEVEL = ContentLibraryPermission.AUTHOR_LEVEL
    READ_LEVEL = ContentLibraryPermission.READ_LEVEL
    NO_ACCESS = None


# General APIs
# ============


def get_libraries_for_user(user, org=None, library_type=None):
    """
    Return content libraries that the user has permission to view.
    """
    filter_kwargs = {}
    if org:
        filter_kwargs['org__short_name'] = org
    if library_type:
        filter_kwargs['type'] = library_type
    qs = ContentLibrary.objects.filter(**filter_kwargs)
    return permissions.perms[permissions.CAN_VIEW_THIS_CONTENT_LIBRARY].filter(user, qs)


def get_metadata_from_index(queryset, text_search=None):
    """
    Take a list of ContentLibrary objects and return metadata stored in
    ContentLibraryIndex.
    """
    metadata = None
    if ContentLibraryIndexer.indexing_is_enabled():
        try:
            library_keys = [str(lib.library_key) for lib in queryset]
            metadata = ContentLibraryIndexer.get_items(library_keys, text_search=text_search)
            metadata_dict = {
                item["id"]: item
                for item in metadata
            }
            metadata = [
                metadata_dict[key]
                if key in metadata_dict
                else None
                for key in library_keys
            ]
        except ElasticConnectionError as e:
            log.exception(e)

    # If ContentLibraryIndex is not available, we query blockstore for a limited set of metadata
    if metadata is None:
        uuids = [lib.bundle_uuid for lib in queryset]
        bundles = get_bundles(uuids=uuids, text_search=text_search)

        if text_search:
            # Bundle APIs can't apply text_search on a bundle's org, so including those results here
            queryset_org_search = queryset.filter(org__short_name__icontains=text_search)
            if queryset_org_search.exists():
                uuids_org_search = [lib.bundle_uuid for lib in queryset_org_search]
                bundles += get_bundles(uuids=uuids_org_search)

        bundle_dict = {
            bundle.uuid: {
                'uuid': bundle.uuid,
                'title': bundle.title,
                'description': bundle.description,
                'version': bundle.latest_version,
            }
            for bundle in bundles
        }
        metadata = [
            bundle_dict[uuid]
            if uuid in bundle_dict
            else None
            for uuid in uuids
        ]

    libraries = [
        ContentLibraryMetadata(
            key=lib.library_key,
            bundle_uuid=metadata[i]['uuid'],
            title=metadata[i]['title'],
            type=lib.type,
            description=metadata[i]['description'],
            version=metadata[i]['version'],
            allow_public_learning=queryset[i].allow_public_learning,
            allow_public_read=queryset[i].allow_public_read,
            num_blocks=metadata[i].get('num_blocks'),
            last_published=metadata[i].get('last_published'),
            has_unpublished_changes=metadata[i].get('has_unpublished_changes'),
            has_unpublished_deletes=metadata[i].get('has_unpublished_deletes'),
            license=lib.license,
        )
        for i, lib in enumerate(queryset)
        if metadata[i] is not None
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
    bundle_metadata = get_bundle(ref.bundle_uuid)
    lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
    num_blocks = len(lib_bundle.get_top_level_usages())
    last_published = lib_bundle.get_last_published_time()
    (has_unpublished_changes, has_unpublished_deletes) = lib_bundle.has_changes()
    return ContentLibraryMetadata(
        key=library_key,
        bundle_uuid=ref.bundle_uuid,
        title=bundle_metadata.title,
        type=ref.type,
        description=bundle_metadata.description,
        num_blocks=num_blocks,
        version=bundle_metadata.latest_version,
        last_published=last_published,
        allow_lti=ref.allow_lti,
        allow_public_learning=ref.allow_public_learning,
        allow_public_read=ref.allow_public_read,
        has_unpublished_changes=has_unpublished_changes,
        has_unpublished_deletes=has_unpublished_deletes,
        license=ref.license,
    )


def create_library(
        collection_uuid, library_type, org, slug, title, description, allow_public_learning, allow_public_read,
        library_license,
):
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
    assert isinstance(collection_uuid, UUID)
    assert isinstance(org, Organization)
    assert not transaction.get_autocommit(), (
        "Call within a django.db.transaction.atomic block so that all created objects are rolled back on error."
    )

    validate_unicode_slug(slug)
    # First, create the blockstore bundle:
    bundle = create_bundle(
        collection_uuid,
        slug=slug,
        title=title,
        description=description,
    )
    # Now create the library reference in our database:
    try:
        ref = ContentLibrary.objects.create(
            org=org,
            slug=slug,
            type=library_type,
            bundle_uuid=bundle.uuid,
            allow_public_learning=allow_public_learning,
            allow_public_read=allow_public_read,
            license=library_license,
        )
    except IntegrityError:
        raise LibraryAlreadyExists(slug)  # lint-amnesty, pylint: disable=raise-missing-from
    CONTENT_LIBRARY_CREATED.send(sender=None, library_key=ref.library_key)
    return ContentLibraryMetadata(
        key=ref.library_key,
        bundle_uuid=bundle.uuid,
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
    ref = ContentLibrary.objects.get_by_key(library_key)

    # Update MySQL model:
    changed = False
    if allow_public_learning is not None:
        ref.allow_public_learning = allow_public_learning
        changed = True
    if allow_public_read is not None:
        ref.allow_public_read = allow_public_read
        changed = True
    if library_type is not None:
        if library_type not in (COMPLEX, ref.type):
            lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
            (has_unpublished_changes, has_unpublished_deletes) = lib_bundle.has_changes()
            if has_unpublished_changes or has_unpublished_deletes:
                raise IncompatibleTypesError(
                    _(
                        'You may not change a library\'s type to {library_type} if it still has unpublished changes.'
                    ).format(library_type=library_type)
                )
            for block in get_library_blocks(library_key):
                if block.usage_key.block_type != library_type:
                    raise IncompatibleTypesError(
                        _(
                            'You can only set a library to {library_type} if all existing blocks are of that type. '
                            'Found incompatible block {block_id} with type {block_type}.'
                        ).format(
                            library_type=library_type,
                            block_type=block.usage_key.block_type,
                            block_id=block.usage_key.block_id,
                        ),
                    )
        ref.type = library_type

        changed = True
    if library_license is not None:
        ref.license = library_license
        changed = True
    if changed:
        ref.save()
    # Update Blockstore:
    fields = {
        # We don't ever read the "slug" value from the Blockstore bundle, but
        # we might as well always do our best to keep it in sync with the "slug"
        # value in the LMS that we do use.
        "slug": ref.slug,
    }
    if title is not None:
        assert isinstance(title, str)
        fields["title"] = title
    if description is not None:
        assert isinstance(description, str)
        fields["description"] = description
    update_bundle(ref.bundle_uuid, **fields)
    CONTENT_LIBRARY_UPDATED.send(sender=None, library_key=ref.library_key)


def delete_library(library_key):
    """
    Delete a content library
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    bundle_uuid = ref.bundle_uuid
    # We can't atomically delete the ref and bundle at the same time.
    # Delete the ref first, then the bundle. An error may cause the bundle not
    # to get deleted, but the library will still be effectively gone from the
    # system, which is a better state than having a reference to a library with
    # no backing blockstore bundle.
    ref.delete()
    CONTENT_LIBRARY_DELETED.send(sender=None, library_key=ref.library_key)
    try:
        delete_bundle(bundle_uuid)
    except:
        log.exception("Failed to delete blockstore bundle %s when deleting library. Delete it manually.", bundle_uuid)
        raise


def get_library_blocks(library_key, text_search=None, block_types=None):
    """
    Get the list of top-level XBlocks in the specified library.

    Returns a list of LibraryXBlockMetadata objects
    """
    metadata = None
    if LibraryBlockIndexer.indexing_is_enabled():
        try:
            filter_terms = {
                'library_key': [str(library_key)],
                'is_child': [False],
            }
            if block_types:
                filter_terms['block_type'] = block_types
            metadata = [
                {
                    **item,
                    "id": LibraryUsageLocatorV2.from_string(item['id']),
                }
                for item in LibraryBlockIndexer.get_items(filter_terms=filter_terms, text_search=text_search)
                if item is not None
            ]
        except ElasticConnectionError as e:
            log.exception(e)

    # If indexing is disabled, or connection to elastic failed
    if metadata is None:
        metadata = []
        ref = ContentLibrary.objects.get_by_key(library_key)
        lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
        usages = lib_bundle.get_top_level_usages()

        for usage_key in usages:
            # For top-level definitions, we can go from definition key to usage key using the following, but this would
            # not work for non-top-level blocks as they may have multiple usages. Top level blocks are guaranteed to
            # have only a single usage in the library, which is part of the definition of top level block.
            def_key = lib_bundle.definition_for_usage(usage_key)
            display_name = get_block_display_name(def_key)
            text_match = (text_search is None or
                          text_search.lower() in display_name.lower() or
                          text_search.lower() in str(usage_key).lower())
            type_match = (block_types is None or usage_key.block_type in block_types)
            if text_match and type_match:
                metadata.append({
                    "id": usage_key,
                    "def_key": def_key,
                    "display_name": display_name,
                    "has_unpublished_changes": lib_bundle.does_definition_have_unpublished_changes(def_key),
                })

    return [
        LibraryXBlockMetadata(
            usage_key=item['id'],
            def_key=item['def_key'],
            display_name=item['display_name'],
            has_unpublished_changes=item['has_unpublished_changes'],
        )
        for item in metadata
    ]


def _lookup_usage_key(usage_key):
    """
    Given a LibraryUsageLocatorV2 (usage key for an XBlock in a content library)
    return the definition key and LibraryBundle
    or raise ContentLibraryBlockNotFound
    """
    assert isinstance(usage_key, LibraryUsageLocatorV2)
    lib_context = get_learning_context_impl(usage_key)
    def_key = lib_context.definition_for_usage(usage_key, force_draft=DRAFT_NAME)
    if def_key is None:
        raise ContentLibraryBlockNotFound(usage_key)
    lib_bundle = LibraryBundle(usage_key.lib_key, def_key.bundle_uuid, draft_name=DRAFT_NAME)
    return def_key, lib_bundle


def get_library_block(usage_key):
    """
    Get metadata (LibraryXBlockMetadata) about one specific XBlock in a library

    To load the actual XBlock instance, use
        openedx.core.djangoapps.xblock.api.load_block()
    instead.
    """
    def_key, lib_bundle = _lookup_usage_key(usage_key)
    return LibraryXBlockMetadata(
        usage_key=usage_key,
        def_key=def_key,
        display_name=get_block_display_name(def_key),
        has_unpublished_changes=lib_bundle.does_definition_have_unpublished_changes(def_key),
    )


def get_library_block_olx(usage_key):
    """
    Get the OLX source of the given XBlock.
    """
    assert isinstance(usage_key, LibraryUsageLocatorV2)
    definition_key = get_library_block(usage_key).def_key
    xml_str = get_bundle_file_data(
        bundle_uuid=definition_key.bundle_uuid,  # pylint: disable=no-member
        path=definition_key.olx_path,  # pylint: disable=no-member
        use_draft=DRAFT_NAME,
    ).decode('utf-8')
    return xml_str


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
    metadata = get_library_block(usage_key)
    block_type = usage_key.block_type
    # Verify that the OLX parses, at least as generic XML:
    node = etree.fromstring(new_olx_str)
    if node.tag != block_type:
        raise ValueError(f"Invalid root tag in OLX, expected {block_type}")
    # Write the new XML/OLX file into the library bundle's draft
    draft = get_or_create_bundle_draft(metadata.def_key.bundle_uuid, DRAFT_NAME)
    write_draft_file(draft.uuid, metadata.def_key.olx_path, new_olx_str.encode('utf-8'))
    # Clear the bundle cache so everyone sees the new block immediately:
    BundleCache(metadata.def_key.bundle_uuid, draft_name=DRAFT_NAME).clear()
    LIBRARY_BLOCK_UPDATED.send(sender=None, library_key=usage_key.context_key, usage_key=usage_key)


def create_library_block(library_key, block_type, definition_id):
    """
    Create a new XBlock in this library of the specified type (e.g. "html").

    The 'definition_id' value (which should be a string like "problem1") will be
    used as both the definition_id and the usage_id.
    """
    assert isinstance(library_key, LibraryLocatorV2)
    ref = ContentLibrary.objects.get_by_key(library_key)
    if ref.type != COMPLEX:
        if block_type != ref.type:
            raise IncompatibleTypesError(
                _('Block type "{block_type}" is not compatible with library type "{library_type}".').format(
                    block_type=block_type, library_type=ref.type,
                )
            )
    lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
    # Total number of blocks should not exceed the maximum allowed
    total_blocks = len(lib_bundle.get_top_level_usages())
    if total_blocks + 1 > settings.MAX_BLOCKS_PER_CONTENT_LIBRARY:
        raise BlockLimitReachedError(
            _("Library cannot have more than {} XBlocks").format(settings.MAX_BLOCKS_PER_CONTENT_LIBRARY)
        )
    # Make sure the proposed ID will be valid:
    validate_unicode_slug(definition_id)
    # Ensure the XBlock type is valid and installed:
    XBlock.load_class(block_type)  # Will raise an exception if invalid
    # Make sure the new ID is not taken already:
    new_usage_id = definition_id  # Since this is a top level XBlock, usage_id == definition_id
    usage_key = LibraryUsageLocatorV2(
        lib_key=library_key,
        block_type=block_type,
        usage_id=new_usage_id,
    )
    library_context = get_learning_context_impl(usage_key)
    if library_context.definition_for_usage(usage_key) is not None:
        raise LibraryBlockAlreadyExists(f"An XBlock with ID '{new_usage_id}' already exists")

    new_definition_xml = f'<{block_type}/>'  # xss-lint: disable=python-wrap-html
    path = f"{block_type}/{definition_id}/definition.xml"
    # Write the new XML/OLX file into the library bundle's draft
    draft = get_or_create_bundle_draft(ref.bundle_uuid, DRAFT_NAME)
    write_draft_file(draft.uuid, path, new_definition_xml.encode('utf-8'))
    # Clear the bundle cache so everyone sees the new block immediately:
    BundleCache(ref.bundle_uuid, draft_name=DRAFT_NAME).clear()
    # Now return the metadata about the new block:
    LIBRARY_BLOCK_CREATED.send(sender=None, library_key=ref.library_key, usage_key=usage_key)
    return get_library_block(usage_key)


def delete_library_block(usage_key, remove_from_parent=True):
    """
    Delete the specified block from this library (and any children it has).

    If the block's definition (OLX file) is within this same library as the
    usage key, both the definition and the usage will be deleted.

    If the usage points to a definition in a linked bundle, the usage will be
    deleted but the link and the linked bundle will be unaffected.

    If the block is in use by some other bundle that links to this one, that
    will not prevent deletion of the definition.

    remove_from_parent: modify the parent to remove the reference to this
        delete block. This should always be true except when this function
        calls itself recursively.
    """
    def_key, lib_bundle = _lookup_usage_key(usage_key)
    # Create a draft:
    draft_uuid = get_or_create_bundle_draft(def_key.bundle_uuid, DRAFT_NAME).uuid
    # Does this block have a parent?
    if usage_key not in lib_bundle.get_top_level_usages() and remove_from_parent:
        # Yes: this is not a top-level block.
        # First need to modify the parent to remove this block as a child.
        raise NotImplementedError
    # Does this block have children?
    block = load_block(usage_key, user=None)
    if block.has_children:
        # Next, recursively call delete_library_block(...) on each child usage
        for child_usage in block.children:
            # Specify remove_from_parent=False to avoid unnecessary work to
            # modify this block's children list when deleting each child, since
            # we're going to delete this block anyways.
            delete_library_block(child_usage, remove_from_parent=False)
    # Delete the definition:
    if def_key.bundle_uuid == lib_bundle.bundle_uuid:
        # This definition is in the library, so delete it:
        path_prefix = lib_bundle.olx_prefix(def_key)
        for bundle_file in get_bundle_files(def_key.bundle_uuid, use_draft=DRAFT_NAME):
            if bundle_file.path.startswith(path_prefix):
                # Delete this file, within this definition's "folder"
                write_draft_file(draft_uuid, bundle_file.path, contents=None)
    else:
        # The definition must be in a linked bundle, so we don't want to delete
        # it; just the <xblock-include /> in the parent, which was already
        # deleted above.
        pass
    # Clear the bundle cache so everyone sees the deleted block immediately:
    lib_bundle.cache.clear()
    LIBRARY_BLOCK_DELETED.send(sender=None, library_key=lib_bundle.library_key, usage_key=usage_key)


def create_library_block_child(parent_usage_key, block_type, definition_id):
    """
    Create a new XBlock definition in this library of the specified type (e.g.
    "html"), and add it as a child of the specified existing block.

    The 'definition_id' value (which should be a string like "problem1") will be
    used as both the definition_id and the usage_id of the child.
    """
    assert isinstance(parent_usage_key, LibraryUsageLocatorV2)
    # Load the parent block to make sure it exists and so we can modify its 'children' field:
    parent_block = load_block(parent_usage_key, user=None)
    if not parent_block.has_children:
        raise ValueError("The specified parent XBlock does not allow child XBlocks.")
    # Create the new block in the library:
    metadata = create_library_block(parent_usage_key.context_key, block_type, definition_id)
    # Set the block as a child.
    # This will effectively "move" the newly created block from being a top-level block in the library to a child.
    include_data = XBlockInclude(link_id=None, block_type=block_type, definition_id=definition_id, usage_hint=None)
    parent_block.runtime.add_child_include(parent_block, include_data)
    parent_block.save()
    ref = ContentLibrary.objects.get_by_key(parent_usage_key.context_key)
    LIBRARY_BLOCK_UPDATED.send(sender=None, library_key=ref.library_key, usage_key=metadata.usage_key)
    return metadata


def get_library_block_static_asset_files(usage_key):
    """
    Given an XBlock in a content library, list all the static asset files
    associated with that XBlock.

    Returns a list of LibraryXBlockStaticFile objects.
    """
    def_key, lib_bundle = _lookup_usage_key(usage_key)
    result = [
        LibraryXBlockStaticFile(path=f.path, url=f.url, size=f.size)
        for f in lib_bundle.get_static_files_for_definition(def_key)
    ]
    result.sort(key=lambda f: f.path)
    return result


def add_library_block_static_asset_file(usage_key, file_name, file_content):
    """
    Upload a static asset file into the library, to be associated with the
    specified XBlock. Will silently overwrite an existing file of the same name.

    file_name should be a name like "doc.pdf". It may optionally contain slashes
        like 'en/doc.pdf'
    file_content should be a binary string.

    Returns a LibraryXBlockStaticFile object.

    Example:
        video_block = UsageKey.from_string("lb:VideoTeam:python-intro:video:1")
        add_library_block_static_asset_file(video_block, "subtitles-en.srt", subtitles.encode('utf-8'))
    """
    assert isinstance(file_content, bytes)
    def_key, lib_bundle = _lookup_usage_key(usage_key)
    if file_name != file_name.strip().strip('/'):
        raise InvalidNameError("file name cannot start/end with / or whitespace.")
    if '//' in file_name or '..' in file_name:
        raise InvalidNameError("Invalid sequence (// or ..) in filename.")
    file_path = lib_bundle.get_static_prefix_for_definition(def_key) + file_name
    # Write the new static file into the library bundle's draft
    draft = get_or_create_bundle_draft(def_key.bundle_uuid, DRAFT_NAME)
    write_draft_file(draft.uuid, file_path, file_content)
    # Clear the bundle cache so everyone sees the new file immediately:
    lib_bundle.cache.clear()
    file_metadata = blockstore_cache.get_bundle_file_metadata_with_cache(
        bundle_uuid=def_key.bundle_uuid, path=file_path, draft_name=DRAFT_NAME,
    )
    LIBRARY_BLOCK_UPDATED.send(sender=None, library_key=lib_bundle.library_key, usage_key=usage_key)
    return LibraryXBlockStaticFile(path=file_metadata.path, url=file_metadata.url, size=file_metadata.size)


def delete_library_block_static_asset_file(usage_key, file_name):
    """
    Delete a static asset file from the library.

    Example:
        video_block = UsageKey.from_string("lb:VideoTeam:python-intro:video:1")
        delete_library_block_static_asset_file(video_block, "subtitles-en.srt")
    """
    def_key, lib_bundle = _lookup_usage_key(usage_key)
    if '..' in file_name:
        raise InvalidNameError("Invalid .. in file name.")
    file_path = lib_bundle.get_static_prefix_for_definition(def_key) + file_name
    # Delete the file from the library bundle's draft
    draft = get_or_create_bundle_draft(def_key.bundle_uuid, DRAFT_NAME)
    write_draft_file(draft.uuid, file_path, contents=None)
    # Clear the bundle cache so everyone sees the new file immediately:
    lib_bundle.cache.clear()
    LIBRARY_BLOCK_UPDATED.send(sender=None, library_key=lib_bundle.library_key, usage_key=usage_key)


def get_allowed_block_types(library_key):  # pylint: disable=unused-argument
    """
    Get a list of XBlock types that can be added to the specified content
    library.
    """
    # This import breaks in the LMS so keep it here. The LMS doesn't generally
    # use content libraries APIs directly but some tests may want to use them to
    # create libraries and then test library learning or course-library integration.
    from cms.djangoapps.contentstore.views.helpers import xblock_type_display_name
    # TODO: return support status and template options
    # See cms/djangoapps/contentstore/views/component.py
    block_types = sorted(name for name, class_ in XBlock.load_classes())
    lib = get_library(library_key)
    if lib.type != COMPLEX:
        # Problem and Video libraries only permit XBlocks of the same name.
        block_types = (name for name in block_types if name == lib.type)
    info = []
    for block_type in block_types:
        display_name = xblock_type_display_name(block_type, None)
        # For now as a crude heuristic, we exclude blocks that don't have a display_name
        if display_name:
            info.append(LibraryXBlockType(block_type=block_type, display_name=display_name))
    return info


def get_bundle_links(library_key):
    """
    Get the list of bundles/libraries linked to this content library.

    Returns LibraryBundleLink objects (defined above).

    Because every content library is a blockstore bundle, it can have "links" to
    other bundles, which may or may not be content libraries. This allows using
    XBlocks (or perhaps even static assets etc.) from another bundle without
    needing to duplicate/copy the data.

    Links always point to a specific published version of the target bundle.
    Links are identified by a slug-like ID, e.g. "link1"
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    links = blockstore_cache.get_bundle_draft_direct_links_cached(ref.bundle_uuid, DRAFT_NAME)
    results = []
    # To be able to quickly get the library ID from the bundle ID for links which point to other libraries, build a map:
    bundle_uuids = {link_data.bundle_uuid for link_data in links.values()}
    libraries_linked = {
        lib.bundle_uuid: lib
        for lib in ContentLibrary.objects.select_related('org').filter(bundle_uuid__in=bundle_uuids)
    }
    for link_name, link_data in links.items():
        # Is this linked bundle a content library?
        try:
            opaque_key = libraries_linked[link_data.bundle_uuid].library_key
        except KeyError:
            opaque_key = None
        try:
            latest_version = blockstore_cache.get_bundle_version_number(link_data.bundle_uuid)
        except BundleNotFound:
            latest_version = 0
        results.append(LibraryBundleLink(
            id=link_name,
            bundle_uuid=link_data.bundle_uuid,
            version=link_data.version,
            latest_version=latest_version,
            opaque_key=opaque_key,
        ))
    return results


def create_bundle_link(library_key, link_id, target_opaque_key, version=None):
    """
    Create a new link to the resource with the specified opaque key.

    For now, only LibraryLocatorV2 opaque keys are supported.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    # Make sure this link ID/name is not already in use:
    links = blockstore_cache.get_bundle_draft_direct_links_cached(ref.bundle_uuid, DRAFT_NAME)
    if link_id in links:
        raise InvalidNameError("That link ID is already in use.")
    # Determine the target:
    if not isinstance(target_opaque_key, LibraryLocatorV2):
        raise TypeError("For now, only LibraryLocatorV2 opaque keys are supported by create_bundle_link")
    target_bundle_uuid = ContentLibrary.objects.get_by_key(target_opaque_key).bundle_uuid
    if version is None:
        version = get_bundle(target_bundle_uuid).latest_version
    # Create the new link:
    draft = get_or_create_bundle_draft(ref.bundle_uuid, DRAFT_NAME)
    set_draft_link(draft.uuid, link_id, target_bundle_uuid, version)
    # Clear the cache:
    LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME).cache.clear()
    CONTENT_LIBRARY_UPDATED.send(sender=None, library_key=library_key)


def update_bundle_link(library_key, link_id, version=None, delete=False):
    """
    Update a bundle's link to point to the specified version of its target
    bundle. Use version=None to automatically point to the latest version.
    Use delete=True to delete the link.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    draft = get_or_create_bundle_draft(ref.bundle_uuid, DRAFT_NAME)
    if delete:
        set_draft_link(draft.uuid, link_id, None, None)
    else:
        links = blockstore_cache.get_bundle_draft_direct_links_cached(ref.bundle_uuid, DRAFT_NAME)
        try:
            link = links[link_id]
        except KeyError:
            raise InvalidNameError("That link does not exist.")  # lint-amnesty, pylint: disable=raise-missing-from
        if version is None:
            version = get_bundle(link.bundle_uuid).latest_version
        set_draft_link(draft.uuid, link_id, link.bundle_uuid, version)
    # Clear the cache:
    LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME).cache.clear()
    CONTENT_LIBRARY_UPDATED.send(sender=None, library_key=library_key)


def publish_changes(library_key):
    """
    Publish all pending changes to the specified library.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    bundle = get_bundle(ref.bundle_uuid)
    if DRAFT_NAME in bundle.drafts:  # pylint: disable=unsupported-membership-test
        draft_uuid = bundle.drafts[DRAFT_NAME]  # pylint: disable=unsubscriptable-object
        commit_draft(draft_uuid)
    else:
        return  # If there is no draft, no action is needed.
    LibraryBundle(library_key, ref.bundle_uuid).cache.clear()
    LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME).cache.clear()
    CONTENT_LIBRARY_UPDATED.send(sender=None, library_key=library_key, update_blocks=True)


def revert_changes(library_key):
    """
    Revert all pending changes to the specified library, restoring it to the
    last published version.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    bundle = get_bundle(ref.bundle_uuid)
    if DRAFT_NAME in bundle.drafts:  # pylint: disable=unsupported-membership-test
        draft_uuid = bundle.drafts[DRAFT_NAME]  # pylint: disable=unsubscriptable-object
        delete_draft(draft_uuid)
    else:
        return  # If there is no draft, no action is needed.
    LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME).cache.clear()
    CONTENT_LIBRARY_UPDATED.send(sender=None, library_key=library_key, update_blocks=True)


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

    def __init__(self, library_key=None, library=None):
        """
        Initialize an import client for a library.

        The method accepts either a library object or a key to a library object.
        """
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
        # Prepend 'c' to allow changing hash without conflicts.
        block_id = f"{modulestore_key.block_id}_c{course_key_id}"
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
        data = XBlockSerializer(block)
        return {'olx': data.olx_str,
                'static_files': {s.name: s for s in data.static_files}}

    def get_export_keys(self, course_key):
        """
        Retrieve the course from modulestore and traverse its content tree.
        """
        course = self.modulestore.get_course(course_key)
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


def import_blocks_create_task(library_key, course_key):
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
        args=(import_task.pk, str(course_key))
    )
    log.info(f"Import block task created: import_task={import_task} "
             f"celery_task={result.id}")
    return import_task
