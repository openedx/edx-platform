"""
Serializers for the Course to Library Import API.
"""

from rest_framework import serializers

from cms.djangoapps.import_from_modulestore.validators import validate_composition_level
from cms.djangoapps.import_from_modulestore.models import Import


class ImportBlocksSerializer(serializers.Serializer):
    """
    Serializer for the import blocks API.
    """

    usage_ids = serializers.ListField(
        child=serializers.CharField(),
        required=True,
    )
    target_library = serializers.CharField(required=True)
    import_uuid = serializers.CharField(required=True)
    composition_level = serializers.CharField(
        required=True,
        validators=[validate_composition_level],
    )
    override = serializers.BooleanField(default=False, required=False)


class ImportSerializer(serializers.ModelSerializer):
    """
    Serializer for the course to library import creation API.
    """

    course_ids = serializers.ListField()
    course_id = serializers.CharField(source='source_key', required=False)

    class Meta:
        model = Import
        fields = [
            'uuid',
            'course_id',
            'course_ids',
            'status',
        ]

    def to_representation(self, instance):
        return {
            'uuid': str(instance.uuid),
            'course_id': str(instance.source_key),
            'status': instance.get_status_display(),
        }
