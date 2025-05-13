"""
Serializers for the content libraries REST API
"""
# pylint: disable=abstract-method
from django.core.validators import validate_unicode_slug
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from opaque_keys import OpaqueKey
from opaque_keys.edx.locator import LibraryContainerLocator, LibraryUsageLocatorV2
from opaque_keys import InvalidKeyError

from openedx_learning.api.authoring_models import Collection
from openedx.core.djangoapps.content_libraries.api.containers import ContainerType
from openedx.core.djangoapps.content_libraries.constants import (
    ALL_RIGHTS_RESERVED,
    LICENSE_OPTIONS,
)
from openedx.core.djangoapps.content_libraries.models import (
    ContentLibraryPermission, ContentLibraryBlockImportTask,
    ContentLibrary
)
from openedx.core.lib.api.serializers import CourseKeyField
from .. import permissions


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
    org = serializers.SlugField(source="key.org")
    slug = serializers.CharField(source="key.slug", validators=(validate_unicode_slug, ))
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    num_blocks = serializers.IntegerField(read_only=True)
    version = serializers.IntegerField(read_only=True)
    last_published = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)
    published_by = serializers.CharField(read_only=True)
    last_draft_created = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)
    last_draft_created_by = serializers.CharField(read_only=True)
    allow_lti = serializers.BooleanField(default=False, read_only=True)
    allow_public_learning = serializers.BooleanField(default=False)
    allow_public_read = serializers.BooleanField(default=False)
    has_unpublished_changes = serializers.BooleanField(read_only=True)
    has_unpublished_deletes = serializers.BooleanField(read_only=True)
    license = serializers.ChoiceField(choices=LICENSE_OPTIONS, default=ALL_RIGHTS_RESERVED)
    can_edit_library = serializers.SerializerMethodField()
    created = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)
    updated = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)

    def get_can_edit_library(self, obj):
        """
        Verifies if the user in request has permission
        to edit a library.
        """
        request = self.context.get('request', None)
        if request is None:
            return False

        user = request.user

        if not user:
            return False

        library_obj = ContentLibrary.objects.get_by_key(obj.key)
        return user.has_perm(permissions.CAN_EDIT_THIS_CONTENT_LIBRARY, obj=library_obj)


class ContentLibraryUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating an existing content library
    """
    # These are the only fields that support changes:
    title = serializers.CharField()
    description = serializers.CharField()
    allow_public_learning = serializers.BooleanField()
    allow_public_read = serializers.BooleanField()
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
    Base serializer for filtering listings on the content library APIs.
    """
    text_search = serializers.CharField(default=None, required=False)
    org = serializers.CharField(default=None, required=False)
    order = serializers.CharField(default=None, required=False)


class CollectionMetadataSerializer(serializers.Serializer):
    """
    Serializer for CollectionMetadata
    """
    key = serializers.CharField()
    title = serializers.CharField()


class PublishableItemSerializer(serializers.Serializer):
    """
    Serializer for any PublishableItem in a library (XBlock, Container, etc.)
    """
    id = serializers.SerializerMethodField()
    display_name = serializers.CharField()
    published_display_name = serializers.CharField(required=False)
    tags_count = serializers.IntegerField(read_only=True)
    last_published = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)
    published_by = serializers.CharField(read_only=True)
    last_draft_created = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)
    last_draft_created_by = serializers.CharField(read_only=True)
    has_unpublished_changes = serializers.BooleanField(read_only=True)
    created = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)
    modified = serializers.DateTimeField(format=DATETIME_FORMAT, read_only=True)

    # When creating a new XBlock in a library, the slug becomes the ID part of
    # the definition key and usage key:
    slug = serializers.CharField(write_only=True)

    collections = CollectionMetadataSerializer(many=True, required=False)
    can_stand_alone = serializers.BooleanField(read_only=True)

    # Fields that are _sometimes_ set, depending on the subclass:
    block_type = serializers.CharField(source="usage_key.block_type", required=False)
    container_type = serializers.CharField(source="container_key.block_type", required=False)

    def get_id(self, obj) -> str:
        """ Get a unique ID for this PublishableItem """
        if hasattr(obj, "usage_key"):
            return str(obj.usage_key)
        elif hasattr(obj, "container_key"):
            return str(obj.container_key)
        return ""


class LibraryXBlockMetadataSerializer(PublishableItemSerializer):
    """
    Serializer for LibraryXBlockMetadata
    """
    block_type = serializers.CharField(source="usage_key.block_type")


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
    # block to. TODO: Remove this, because we don't support it.
    parent_block = serializers.CharField(required=False)

    block_type = serializers.CharField()

    # TODO: Rename to ``block_id`` or ``slug``. The Learning Core XBlock runtime
    # doesn't use definition_ids, but this field is really just about requesting
    # a specific block_id, e.g. the "best_tropical_vacation_spots" portion of a
    # problem with UsageKey:
    #   lb:Axim:VacationsLib:problem:best_tropical_vacation_spots
    #
    # It doesn't look like the frontend actually uses this to put meaningful
    # slugs at the moment, but hopefully we can change this soon.
    definition_id = serializers.CharField(validators=(validate_unicode_slug, ))

    # Optional param specified when pasting data from clipboard instead of
    # creating new block from scratch
    staged_content = serializers.CharField(required=False)

    # Optional param defaults to True, set to False if block is being created under a container.
    can_stand_alone = serializers.BooleanField(required=False, default=True)


class LibraryXBlockOlxSerializer(serializers.Serializer):
    """
    Serializer for representing an XBlock's OLX
    """
    olx = serializers.CharField()
    version_num = serializers.IntegerField(read_only=True, required=False)


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


class LibraryXBlockStaticFilesSerializer(serializers.Serializer):
    """
    Serializer representing a static file associated with an XBlock

    Serializes a LibraryXBlockStaticFile (or a BundleFile)
    """
    files = LibraryXBlockStaticFileSerializer(many=True)


class LibraryContainerMetadataSerializer(PublishableItemSerializer):
    """
    Serializer for Containers like Sections, Subsections, Units

    Converts from ContainerMetadata to JSON-compatible data
    """
    # Use 'source' to get this as a string, not an enum value instance which the container_type field has.
    container_type = serializers.CharField(source="container_key.container_type")

    # When creating a new container in a library, the slug becomes the ID part of
    # the definition key and usage key:
    slug = serializers.CharField(write_only=True, required=False)

    def to_internal_value(self, data):
        """
        Convert JSON-ish data back to native python types.
        Returns a dictionary, not a ContainerMetadata instance.
        """
        result = super().to_internal_value(data)
        result["container_type"] = ContainerType(data["container_type"])
        return result


class LibraryContainerUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating metadata for Containers like Sections, Subsections, Units
    """
    display_name = serializers.CharField()


class ContentLibraryBlockImportTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for a Content Library block import task.
    """

    org = serializers.SerializerMethodField()

    def get_org(self, obj):
        return obj.course_id.org

    class Meta:
        model = ContentLibraryBlockImportTask
        fields = '__all__'


class ContentLibraryBlockImportTaskCreateSerializer(serializers.Serializer):
    """
    Serializer to create a new block import task.

    The serializer accepts the following parameter:

    - The courseware course key to import blocks from.
    """

    course_key = CourseKeyField()


class ContentLibraryCollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for a Content Library Collection
    """

    class Meta:
        model = Collection
        fields = '__all__'


class ContentLibraryCollectionUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating a Collection in a Content Library
    """

    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)


class UsageKeyV2Serializer(serializers.BaseSerializer):
    """
    Serializes a library Component (XBlock) key.
    """
    def to_representation(self, value: LibraryUsageLocatorV2) -> str:
        """
        Returns the LibraryUsageLocatorV2 value as a string.
        """
        return str(value)

    def to_internal_value(self, value: str) -> LibraryUsageLocatorV2:
        """
        Returns a LibraryUsageLocatorV2 from the string value.

        Raises ValidationError if invalid LibraryUsageLocatorV2.
        """
        try:
            return LibraryUsageLocatorV2.from_string(value)
        except InvalidKeyError as err:
            raise ValidationError from err


class ContentLibraryComponentKeysSerializer(serializers.Serializer):
    """
    Serializer for adding/removing Components to/from a Collection.
    """

    usage_keys = serializers.ListField(child=UsageKeyV2Serializer(), allow_empty=False)


class OpaqueKeySerializer(serializers.BaseSerializer):
    """
    Serializes a OpaqueKey with the correct class.
    """
    def to_representation(self, value: OpaqueKey) -> str:
        """
        Returns the OpaqueKey value as a string.
        """
        return str(value)

    def to_internal_value(self, value: str) -> OpaqueKey:
        """
        Returns a LibraryUsageLocatorV2 or a LibraryContainerLocator from the string value.

        Raises ValidationError if invalid UsageKeyV2 or LibraryContainerLocator.
        """
        try:
            return LibraryUsageLocatorV2.from_string(value)
        except InvalidKeyError:
            try:
                return LibraryContainerLocator.from_string(value)
            except InvalidKeyError as err:
                raise ValidationError from err


class ContentLibraryItemKeysSerializer(serializers.Serializer):
    """
    Serializer for adding/removing items to/from a Collection.
    """

    usage_keys = serializers.ListField(child=OpaqueKeySerializer(), allow_empty=False)


class ContentLibraryItemCollectionsUpdateSerializer(serializers.Serializer):
    """
    Serializer for adding/removing Collections to/from a Library Item (component, unit, etc..).
    """

    collection_keys = serializers.ListField(child=serializers.CharField(), allow_empty=True)
