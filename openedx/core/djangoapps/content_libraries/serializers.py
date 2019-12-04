"""
Serializers for the content libraries REST API
"""
# pylint: disable=abstract-method
from __future__ import absolute_import, division, print_function, unicode_literals

from django.core.validators import validate_unicode_slug
from rest_framework import serializers

from openedx.core.lib import blockstore_api


class ContentLibraryMetadataSerializer(serializers.Serializer):
    """
    Serializer for ContentLibraryMetadata
    """
    # We rename the primary key field to "id" in the REST API since API clients
    # often implement magic functionality for fields with that name, and "key"
    # is a reserved prop name in React
    id = serializers.CharField(source="key", read_only=True)
    org = serializers.SlugField(source="key.org")
    slug = serializers.CharField(source="key.slug", validators=(validate_unicode_slug, ))
    bundle_uuid = serializers.UUIDField(format='hex_verbose', read_only=True)
    collection_uuid = serializers.UUIDField(format='hex_verbose', write_only=True)
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    version = serializers.IntegerField(read_only=True)
    has_unpublished_changes = serializers.BooleanField(read_only=True)
    has_unpublished_deletes = serializers.BooleanField(read_only=True)


class ContentLibraryUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating an existing content library
    """
    # These are the only fields that support changes:
    title = serializers.CharField()
    description = serializers.CharField()


class LibraryXBlockMetadataSerializer(serializers.Serializer):
    """
    Serializer for LibraryXBlockMetadata
    """
    id = serializers.CharField(source="usage_key", read_only=True)
    def_key = serializers.CharField(read_only=True)
    block_type = serializers.CharField(source="def_key.block_type")
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
