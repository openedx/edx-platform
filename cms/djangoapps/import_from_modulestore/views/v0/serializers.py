"""
Serializers for the Course to Library Import API.
"""

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import LearningContextKey
from opaque_keys.edx.locator import LibraryLocatorV2
from rest_framework import serializers
from user_tasks.serializers import StatusSerializer

from cms.djangoapps.import_from_modulestore.models import Import
from cms.djangoapps.import_from_modulestore.validators import validate_composition_level, validate_usage_keys_to_import


class ImportSerializer(serializers.ModelSerializer):
    """
    Serializer for the course to library import creation API.
    """

    target = serializers.CharField(
        help_text="The target library key to import into.",
        required=True,
    )
    usage_keys_string = serializers.CharField(
        help_text="Comma separated list of usage keys to import.",
        required=True,
    )

    class Meta:
        model = Import
        fields = [
            'source_key',
            'target',
            'usage_keys_string',
            'composition_level',
            'override',
        ]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        if request and request.method != 'POST':
            fields.pop('target', None)
            fields.pop('usage_keys_string', None)
        return fields

    def validate_source_key(self, value):
        """
        Validate the source key format.
        """
        try:
            LearningContextKey.from_string(value)
        except InvalidKeyError as exc:
            raise serializers.ValidationError(f"Invalid source key: {str(exc)}") from exc
        return value

    def validate_target(self, value):
        """
        Validate the target library key format.
        """
        try:
            LibraryLocatorV2.from_string(value)
        except InvalidKeyError as exc:
            raise serializers.ValidationError(f"Invalid target library key: {str(exc)}") from exc
        return value

    def validate_usage_keys_string(self, value):
        """
        Validate the usage keys string format and split into a list.
        """
        try:
            validate_usage_keys_to_import(value.split(','))
        except InvalidKeyError as exc:
            raise serializers.ValidationError(f"Invalid usage keys: {str(exc)}") from exc
        return value.split(',')

    def validate_composition_level(self, value):
        """
        Validate the composition level.
        """
        try:
            validate_composition_level(value)
        except ValueError as exc:
            raise serializers.ValidationError(f"Invalid composition level: {str(exc)}") from exc
        return value


class StatusWithImportSerializer(StatusSerializer):
    """
    Serializer for the import task status.
    """

    import_event = ImportSerializer()

    class Meta:
        model = StatusSerializer.Meta.model
        fields = [*StatusSerializer.Meta.fields, 'import_event']
