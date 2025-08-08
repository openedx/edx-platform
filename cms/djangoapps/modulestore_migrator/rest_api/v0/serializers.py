"""
Serializers for the Course to Library Import API.
"""

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import LearningContextKey
from opaque_keys.edx.locator import LibraryLocatorV2
from rest_framework import serializers
from user_tasks.serializers import StatusSerializer

from cms.djangoapps.modulestore_migrator.data import CompositionLevel
from cms.djangoapps.modulestore_migrator.models import ModulestoreMigration


class ModulestoreMigrationSerializer(serializers.ModelSerializer):
    """
    Serializer for the course to library import creation API.
    """

    source = serializers.CharField(
        help_text="The source course or legacy library key to import from.",
        required=True,
        source='source.key',
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
    replace_existing = serializers.BooleanField(
        help_text="If true, replace existing content in the target library.",
        required=False,
        default=False,
    )
    target_collection_slug = serializers.CharField(
        help_text="The target collection slug within the library to import into. Optional.",
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = ModulestoreMigration
        fields = [
            'source',
            'target',
            'target_collection_slug',
            'composition_level',
            'replace_existing',
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


class StatusWithModulestoreMigrationSerializer(StatusSerializer):
    """
    Serializer for the import task status.
    """

    modulestoremigration = ModulestoreMigrationSerializer()

    class Meta:
        model = StatusSerializer.Meta.model
        fields = [*StatusSerializer.Meta.fields, 'modulestoremigration']
