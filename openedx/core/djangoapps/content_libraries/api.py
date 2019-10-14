"""
Python API for content libraries.

Unless otherwise specified, all APIs in this file deal with the DRAFT version
of the content library.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from uuid import UUID
import logging

import attr
from django.core.validators import validate_unicode_slug
from django.db import IntegrityError
from lxml import etree
from opaque_keys.edx.locator import BundleDefinitionLocator, LibraryLocatorV2, LibraryUsageLocatorV2
from organizations.models import Organization
import six
from xblock.core import XBlock
from xblock.exceptions import XBlockNotFoundError

from openedx.core.djangoapps.content_libraries.library_bundle import LibraryBundle
from openedx.core.djangoapps.xblock.api import get_block_display_name, load_block
from openedx.core.djangoapps.xblock.learning_context.manager import get_learning_context_impl
from openedx.core.djangoapps.xblock.runtime.olx_parsing import XBlockInclude
from openedx.core.lib.blockstore_api import (
    get_bundle,
    get_bundle_file_data,
    get_bundle_files,
    get_or_create_bundle_draft,
    create_bundle,
    update_bundle,
    delete_bundle,
    write_draft_file,
    commit_draft,
    delete_draft,
)
from openedx.core.djangolib import blockstore_cache
from openedx.core.djangolib.blockstore_cache import BundleCache
from .models import ContentLibrary, ContentLibraryPermission

log = logging.getLogger(__name__)

# This API is only used in Studio, so we always work with this draft of any
# content library bundle:
DRAFT_NAME = 'studio_draft'

# Exceptions:
ContentLibraryNotFound = ContentLibrary.DoesNotExist


class ContentLibraryBlockNotFound(XBlockNotFoundError):
    """ XBlock not found in the content library """


class LibraryAlreadyExists(KeyError):
    """ A library with the specified slug already exists """


class LibraryBlockAlreadyExists(KeyError):
    """ An XBlock with that ID already exists in the library """


class InvalidNameError(ValueError):
    """ The specified name/identifier is not valid """


# Models:

@attr.s
class ContentLibraryMetadata(object):
    """
    Class that represents the metadata about a content library.
    """
    key = attr.ib(type=LibraryLocatorV2)
    bundle_uuid = attr.ib(type=UUID)
    title = attr.ib("")
    description = attr.ib("")
    version = attr.ib(0)
    has_unpublished_changes = attr.ib(False)
    # has_unpublished_deletes will be true when the draft version of the library's bundle
    # contains deletes of any XBlocks that were in the most recently published version
    has_unpublished_deletes = attr.ib(False)


@attr.s
class LibraryXBlockMetadata(object):
    """
    Class that represents the metadata about an XBlock in a content library.
    """
    usage_key = attr.ib(type=LibraryUsageLocatorV2)
    def_key = attr.ib(type=BundleDefinitionLocator)
    display_name = attr.ib("")
    has_unpublished_changes = attr.ib(False)


@attr.s
class LibraryXBlockStaticFile(object):
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
class LibraryXBlockType(object):
    """
    An XBlock type that can be added to a content library
    """
    block_type = attr.ib("")
    display_name = attr.ib("")


class AccessLevel(object):
    """ Enum defining library access levels/permissions """
    ADMIN_LEVEL = ContentLibraryPermission.ADMIN_LEVEL
    AUTHOR_LEVEL = ContentLibraryPermission.AUTHOR_LEVEL
    READ_LEVEL = ContentLibraryPermission.READ_LEVEL
    NO_ACCESS = None


def list_libraries():
    """
    TEMPORARY method for testing. Lists all content libraries.
    This should be replaced with a method for listing all libraries that belong
    to a particular user, and/or has permission to view. This method makes at
    least one HTTP call per library so should only be used for development.
    """
    refs = ContentLibrary.objects.all()[:1000]
    return [get_library(ref.library_key) for ref in refs]


def get_library(library_key):
    """
    Get the library with the specified key. Does not check permissions.
    returns a ContentLibraryMetadata instance.

    Raises ContentLibraryNotFound if the library doesn't exist.
    """
    assert isinstance(library_key, LibraryLocatorV2)
    ref = ContentLibrary.objects.get_by_key(library_key)
    bundle_metadata = get_bundle(ref.bundle_uuid)
    lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
    (has_unpublished_changes, has_unpublished_deletes) = lib_bundle.has_changes()
    return ContentLibraryMetadata(
        key=library_key,
        bundle_uuid=ref.bundle_uuid,
        title=bundle_metadata.title,
        description=bundle_metadata.description,
        version=bundle_metadata.latest_version,
        has_unpublished_changes=has_unpublished_changes,
        has_unpublished_deletes=has_unpublished_deletes,
    )


def create_library(collection_uuid, org, slug, title, description):
    """
    Create a new content library.

    org: an organizations.models.Organization instance

    slug: a slug for this library like 'physics-problems'

    title: title for this library

    description: description of this library

    Returns a ContentLibraryMetadata instance.
    """
    assert isinstance(collection_uuid, UUID)
    assert isinstance(org, Organization)
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
            bundle_uuid=bundle.uuid,
            allow_public_learning=True,
            allow_public_read=True,
        )
    except IntegrityError:
        delete_bundle(bundle.uuid)
        raise LibraryAlreadyExists(slug)
    return ContentLibraryMetadata(
        key=ref.library_key,
        bundle_uuid=bundle.uuid,
        title=title,
        description=description,
        version=0,
    )


def set_library_user_permissions(library_key, user, access_level):
    """
    Change the specified user's level of access to this library.

    access_level should be one of the AccessLevel values defined above.
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    if access_level is None:
        ref.authorized_users.filter(user=user).delete()
    else:
        ContentLibraryPermission.objects.update_or_create(user=user, library=ref, access_level=access_level)


def update_library(library_key, title=None, description=None):
    """
    Update a library's title or description.
    (Slug cannot be changed as it would break IDs throughout the system.)

    A value of None means "don't change".
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    fields = {
        # We don't ever read the "slug" value from the Blockstore bundle, but
        # we might as well always do our best to keep it in sync with the "slug"
        # value in the LMS that we do use.
        "slug": ref.slug,
    }
    if title is not None:
        assert isinstance(title, six.string_types)
        fields["title"] = title
    if description is not None:
        assert isinstance(description, six.string_types)
        fields["description"] = description
    update_bundle(ref.bundle_uuid, **fields)


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
    try:
        delete_bundle(bundle_uuid)
    except:
        log.exception("Failed to delete blockstore bundle %s when deleting library. Delete it manually.", bundle_uuid)
        raise


def get_library_blocks(library_key):
    """
    Get the list of top-level XBlocks in the specified library.

    Returns a list of LibraryXBlockMetadata objects
    """
    ref = ContentLibrary.objects.get_by_key(library_key)
    lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
    usages = lib_bundle.get_top_level_usages()
    blocks = []
    for usage_key in usages:
        # For top-level definitions, we can go from definition key to usage key using the following, but this would not
        # work for non-top-level blocks as they may have multiple usages. Top level blocks are guaranteed to have only
        # a single usage in the library, which is part of the definition of top level block.
        def_key = lib_bundle.definition_for_usage(usage_key)
        blocks.append(LibraryXBlockMetadata(
            usage_key=usage_key,
            def_key=def_key,
            display_name=get_block_display_name(def_key),
            has_unpublished_changes=lib_bundle.does_definition_have_unpublished_changes(def_key),
        ))
    return blocks


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
        raise ValueError("Invalid root tag in OLX, expected {}".format(block_type))
    # Write the new XML/OLX file into the library bundle's draft
    draft = get_or_create_bundle_draft(metadata.def_key.bundle_uuid, DRAFT_NAME)
    write_draft_file(draft.uuid, metadata.def_key.olx_path, new_olx_str.encode('utf-8'))
    # Clear the bundle cache so everyone sees the new block immediately:
    BundleCache(metadata.def_key.bundle_uuid, draft_name=DRAFT_NAME).clear()


def create_library_block(library_key, block_type, definition_id):
    """
    Create a new XBlock in this library of the specified type (e.g. "html").

    The 'definition_id' value (which should be a string like "problem1") will be
    used as both the definition_id and the usage_id.
    """
    assert isinstance(library_key, LibraryLocatorV2)
    ref = ContentLibrary.objects.get_by_key(library_key)
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
        raise LibraryBlockAlreadyExists("An XBlock with ID '{}' already exists".format(new_usage_id))

    new_definition_xml = '<{}/>'.format(block_type)  # xss-lint: disable=python-wrap-html
    path = "{}/{}/definition.xml".format(block_type, definition_id)
    # Write the new XML/OLX file into the library bundle's draft
    draft = get_or_create_bundle_draft(ref.bundle_uuid, DRAFT_NAME)
    write_draft_file(draft.uuid, path, new_definition_xml.encode('utf-8'))
    # Clear the bundle cache so everyone sees the new block immediately:
    BundleCache(ref.bundle_uuid, draft_name=DRAFT_NAME).clear()
    # Now return the metadata about the new block:
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
    assert isinstance(file_content, six.binary_type)
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


def get_allowed_block_types(library_key):  # pylint: disable=unused-argument
    """
    Get a list of XBlock types that can be added to the specified content
    library. For now, the result is the same regardless of which library is
    specified, but that may change in the future.
    """
    # This import breaks in the LMS so keep it here. The LMS doesn't generally
    # use content libraries APIs directly but some tests may want to use them to
    # create libraries and then test library learning or course-library integration.
    from cms.djangoapps.contentstore.views.helpers import xblock_type_display_name
    # TODO: return support status and template options
    # See cms/djangoapps/contentstore/views/component.py
    block_types = sorted(name for name, class_ in XBlock.load_classes())
    info = []
    for block_type in block_types:
        display_name = xblock_type_display_name(block_type, None)
        # For now as a crude heuristic, we exclude blocks that don't have a display_name
        if display_name:
            info.append(LibraryXBlockType(block_type=block_type, display_name=display_name))
    return info


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
