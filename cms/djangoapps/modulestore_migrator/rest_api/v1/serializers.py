"""
Serializers for the Course to Library Import API.
"""

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import LearningContextKey
from opaque_keys.edx.locator import LibraryLocatorV2
from rest_framework import serializers
from user_tasks.serializers import StatusSerializer

from cms.djangoapps.modulestore_migrator.data import CompositionLevel, RepeatHandlingStrategy
from cms.djangoapps.modulestore_migrator.models import ModulestoreMigration


class ModulestoreMigrationSerializer(serializers.Serializer):
    """
    Serializer for the course or legacylibrary to library V2 import creation API.
    """

    source = serializers.CharField(  # type: ignore[assignment]
        help_text="The source course or legacy library key to import from.",
        required=True,
    )
    target = serializers.CharField(
        help_text="The target content library V2 key to import into.",
        required=True,
    )
    composition_level = serializers.ChoiceField(
        help_text="The composition level to import the content at.",
        choices=CompositionLevel.supported_choices(),
        required=False,
        default=CompositionLevel.Component.value,
    )
    repeat_handling_strategy = serializers.ChoiceField(
        help_text="If a piece of content already exists in the content library, choose how to handle it.",
        choices=RepeatHandlingStrategy.supported_choices(),
        required=False,
        default=RepeatHandlingStrategy.Skip.value,
    )
    preserve_url_slugs = serializers.BooleanField(
        help_text="If true, current slugs will be preserved.",
        required=False,
        default=True,
    )
    target_collection_slug = serializers.CharField(
        help_text="The target collection slug within the library to import into. Optional.",
        required=False,
        allow_blank=True,
        default=None,
    )
    forward_source_to_target = serializers.BooleanField(
        help_text="Forward references of this block source over to the target of this block migration.",
        required=False,
        default=False,
    )
    is_failed = serializers.BooleanField(
        help_text="It is true if this migration is failed",
        required=False,
        default=False,
    )

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method != 'POST':
            fields.pop('target', None)
            fields.pop('target_collection_slug', None)
        return fields

    def validate_source(self, value):
        """
        Validate the source key format.
        """
        try:
            return LearningContextKey.from_string(value)
        except InvalidKeyError as exc:
            raise serializers.ValidationError(f"Invalid source key: {str(exc)}") from exc

    def validate_target(self, value):
        """
        Validate the target library key format.
        """
        try:
            return LibraryLocatorV2.from_string(value)
        except InvalidKeyError as exc:
            raise serializers.ValidationError(f"Invalid target library key: {str(exc)}") from exc

    def get_forward_source_to_target(self, obj: ModulestoreMigration):
        """
        Check if the source block was forwarded to the target.
        """
        return obj.id == obj.source.forwarded_id

    def to_representation(self, instance):
        """
        Override to customize the serialized representation.
        """
        data = super().to_representation(instance)
        # Custom logic for forward_source_to_target during serialization
        data['forward_source_to_target'] = self.get_forward_source_to_target(instance)
        return data


class BulkModulestoreMigrationSerializer(ModulestoreMigrationSerializer):
    """
    Serializer for a bulk migration (of several courses or legacy libraries) to a V2 library.
    """
    sources = serializers.ListField(
        child=serializers.CharField(),
        help_text="The list of sources course or legacy library keys to import from.",
        required=True,
    )

    target_collection_slug_list = serializers.ListField(
        child=serializers.CharField(),
        help_text="The list of target collection slugs within the library to import into. Optional.",
        required=False,
        allow_empty=True,
        default=None,
    )

    create_collections = serializers.BooleanField(
        help_text=(
            "If true and `target_collection_slug_list` is not set, "
            "create the collections in the library where the import will be made"
        ),
        required=False,
        default=False,
    )

    def get_fields(self):
        fields = super().get_fields()
        fields.pop("source", None)
        fields.pop("target_collection_slug", None)
        return fields

    def validate_sources(self, value):
        """
        Validate all the source key format
        """
        validated_sources = []
        for v in value:
            try:
                validated_sources.append(LearningContextKey.from_string(v))
            except InvalidKeyError as exc:
                raise serializers.ValidationError(f"Invalid source key: {str(exc)}") from exc
        return validated_sources

    def to_representation(self, instance):
        """
        Override to customize the serialized representation.
        """
        if isinstance(instance, list):
            return [super().to_representation(obj) for obj in instance]
        return super().to_representation(instance)


class StatusWithModulestoreMigrationsSerializer(StatusSerializer):
    """
    Serializer for the import task status, including 1+ migration objects.
    """

    parameters = ModulestoreMigrationSerializer(source='migrations', many=True)

    class Meta:
        model = StatusSerializer.Meta.model
        fields = [*StatusSerializer.Meta.fields, 'uuid', 'parameters']

    def get_fields(self):
        """
        Remove unwanted fields
        """
        fields = super().get_fields()
        fields.pop('name', None)
        return fields


class MigrationInfoSerializer(serializers.Serializer):
    """
    Serializer for the migration info
    """

    source_key = serializers.CharField(source="key")
    target_key = serializers.CharField(source="migrations__target__key")
    target_title = serializers.CharField(source="migrations__target__title")
    target_collection_key = serializers.CharField(
        source="migrations__target_collection__key",
        allow_null=True
    )
    target_collection_title = serializers.CharField(
        source="migrations__target_collection__title",
        allow_null=True
    )


class MigrationInfoResponseSerializer(serializers.Serializer):
    """
    Serializer for the migrations info view response
    """
    def to_representation(self, instance):
        return {
            str(key): MigrationInfoSerializer(value, many=True).data
            for key, value in instance.items()
        }
