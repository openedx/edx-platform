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


class ModulestoreMigrationSerializer(serializers.ModelSerializer):
    """
    Serializer for the course to library import creation API.
    """

    source = serializers.CharField(  # type: ignore[assignment]
        help_text="The source course or legacy library key to import from.",
        required=True,
    )
    target = serializers.CharField(
        help_text="The target library key to import into.",
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

    class Meta:
        model = ModulestoreMigration
        fields = [
            'source',
            'target',
            'target_collection_slug',
            'composition_level',
            'repeat_handling_strategy',
            'preserve_url_slugs',
            'forward_source_to_target',
        ]

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
        Override to customize the serialized representation."""
        data = super().to_representation(instance)
        # Custom logic for forward_source_to_target during serialization
        data['forward_source_to_target'] = self.get_forward_source_to_target(instance)
        return data


class StatusWithModulestoreMigrationSerializer(StatusSerializer):
    """
    Serializer for the import task status.
    """

    parameters = ModulestoreMigrationSerializer(source='modulestoremigration')

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
