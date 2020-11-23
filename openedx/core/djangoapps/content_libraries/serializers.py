"""
Serializers for the content libraries REST API
"""
# pylint: disable=abstract-method
from django.core.validators import validate_unicode_slug
from rest_framework import serializers

from openedx.core.djangoapps.content_libraries.constants import (
    LIBRARY_TYPES,
    COMPLEX,
    ALL_RIGHTS_RESERVED,
    LICENSE_OPTIONS,
)
from openedx.core.djangoapps.content_libraries.models import ContentLibraryPermission
from openedx.core.lib import blockstore_api

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class ContentLibraryMetadataSerializer(serializers.Serializer):
    """
    Serializer for ContentLibraryMetadata
    """
    # We rename the primary key field to "id" in the REST API since API clients
    # often implement magic functionality for fields with that name, and "key"
    # is a reserved prop name in React. This 'id' field is a string that
    # begins with 'lib:'. (The numeric ID of the ContentLibrary object in MySQL
    # is not exposed via this API.)
    id = serializers.CharField(source="key", read_only=True)
    type = serializers.ChoiceField(choices=LIBRARY_TYPES, default=COMPLEX)
    org = serializers.SlugField(source="key.org")
    slug = serializers.CharField(source="key.slug", validators=(validate_unicode_slug, ))
    bundle_uuid = serializers.UUIDField(format='hex_verbose', read_only=True)
    collection_uuid = serializers.UUIDField(format='hex_verbose', write_only=True)
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    num_blocks = serializers.IntegerField(read_only=True)
    version = serializers.IntegerField(read_only=True)
    last_published = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)
    allow_public_learning = serializers.BooleanField(default=False)
    allow_public_read = serializers.BooleanField(default=False)
    has_unpublished_changes = serializers.BooleanField(read_only=True)
    has_unpublished_deletes = serializers.BooleanField(read_only=True)
    license = serializers.ChoiceField(choices=LICENSE_OPTIONS, default=ALL_RIGHTS_RESERVED)


class ContentLibraryUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating an existing content library
    """
    # These are the only fields that support changes:
    title = serializers.CharField()
    description = serializers.CharField()
    allow_public_learning = serializers.BooleanField()
    allow_public_read = serializers.BooleanField()
    type = serializers.ChoiceField(choices=LIBRARY_TYPES)
    license = serializers.ChoiceField(choices=LICENSE_OPTIONS)


class ContentLibraryPermissionLevelSerializer(serializers.Serializer):
    """
    Serializer for the "Access Level" of a ContentLibraryPermission object.

    This is used when updating a user or group's permissions re some content
    library.
    """
    access_level = serializers.ChoiceField(choices=ContentLibraryPermission.ACCESS_LEVEL_CHOICES)


class ContentLibraryAddPermissionByEmailSerializer(serializers.Serializer):
    """
    Serializer for adding a new user and granting their access level via their email address.
    """
    access_level = serializers.ChoiceField(choices=ContentLibraryPermission.ACCESS_LEVEL_CHOICES)
    email = serializers.EmailField()


class ContentLibraryPermissionSerializer(ContentLibraryPermissionLevelSerializer):
    """
    Serializer for a ContentLibraryPermission object, which grants either a user
    or a group permission to view a content library.
    """
    email = serializers.EmailField(source="user.email", read_only=True, default=None)
    username = serializers.CharField(source="user.username", read_only=True, default=None)
    group_name = serializers.CharField(source="group.name", allow_null=True, allow_blank=False, default=None)


class ContentLibraryFilterSerializer(serializers.Serializer):
    """
    Serializer for filtering library listings.
    """
    text_search = serializers.CharField(default=None, required=False)
    org = serializers.CharField(default=None, required=False)
    type = serializers.ChoiceField(choices=LIBRARY_TYPES, default=None, required=False)


class LibraryXBlockMetadataSerializer(serializers.Serializer):
    """
    Serializer for LibraryXBlockMetadata
    """
    id = serializers.CharField(source="usage_key", read_only=True)
    def_key = serializers.CharField(read_only=True)
    block_type = serializers.CharField(source="usage_key.block_type")
    display_name = serializers.CharField(read_only=True)
    has_unpublished_changes = serializers.BooleanField(read_only=True)
    # When creating a new XBlock in a library, the slug becomes the ID part of
    # the definition key and usage key:
    slug = serializers.CharField(write_only=True)


class LibraryXBlockTypeSerializer(serializers.Serializer):
    """
    Serializer for LibraryXBlockType
    """
    block_type = serializers.CharField()
    display_name = serializers.CharField()


class LibraryBundleLinkSerializer(serializers.Serializer):
    """
    Serializer for a link from a content library blockstore bundle to another
    blockstore bundle.
    """
    id = serializers.SlugField()  # Link name
    bundle_uuid = serializers.UUIDField(format='hex_verbose', read_only=True)
    # What version of this bundle we are currently linking to.
    # This is never NULL but can optionally be set to null when creating a new link, which means "use latest version."
    version = serializers.IntegerField(allow_null=True)
    # What the latest version of the linked bundle is:
    # (if latest_version > version), the link can be "updated" to the latest version.
    latest_version = serializers.IntegerField(read_only=True)
    # Opaque key: If the linked bundle is a library or other learning context whose opaque key we can deduce, then this
    # is the key. If we don't know what type of blockstore bundle this link is pointing to, then this is blank.
    opaque_key = serializers.CharField()


class LibraryBundleLinkUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating an existing link in a content library blockstore
    bundle.
    """
    version = serializers.IntegerField(allow_null=True)


class LibraryXBlockCreationSerializer(serializers.Serializer):
    """
    Serializer for adding a new XBlock to a content library
    """
    # Parent block: optional usage key of an existing block to add this child
    # block to.
    parent_block = serializers.CharField(required=False)
    block_type = serializers.CharField()
    definition_id = serializers.SlugField()


class LibraryXBlockOlxSerializer(serializers.Serializer):
    """
    Serializer for representing an XBlock's OLX
    """
    olx = serializers.CharField()


class LibraryXBlockStaticFileSerializer(serializers.Serializer):
    """
    Serializer representing a static file associated with an XBlock

    Serializes a LibraryXBlockStaticFile (or a BundleFile)
    """
    path = serializers.CharField()
    # Publicly accessible URL where the file can be downloaded.
    # Must be an absolute URL.
    url = serializers.URLField()
    size = serializers.IntegerField(min_value=0)

    def to_representation(self, instance):
        """
        Generate the serialized representation of this static asset file.
        """
        result = super(LibraryXBlockStaticFileSerializer, self).to_representation(instance)
        # Make sure the URL is one that will work from the user's browser,
        # not one that only works from within a docker container:
        result['url'] = blockstore_api.force_browser_url(result['url'])
        return result


class LibraryXBlockStaticFilesSerializer(serializers.Serializer):
    """
    Serializer representing a static file associated with an XBlock

    Serializes a LibraryXBlockStaticFile (or a BundleFile)
    """
    files = LibraryXBlockStaticFileSerializer(many=True)
