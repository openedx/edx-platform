"""
Serializers for the Course to Library Import API.
"""

from rest_framework import serializers

from cms.djangoapps.course_to_library_import.models import CourseToLibraryImport
from cms.djangoapps.course_to_library_import.validators import validate_composition_level


class ImportBlocksSerializer(serializers.Serializer):
    """
    Serializer for the import blocks API.
    """

    library_key = serializers.CharField(required=True)
    usage_ids = serializers.ListField(
        child=serializers.CharField(),
        required=True,
    )
    course_id = serializers.CharField(required=True)
    import_id = serializers.CharField(required=True)
    composition_level = serializers.CharField(
        required=True,
        validators=[validate_composition_level],
    )
    override = serializers.BooleanField(default=False, required=False)

    def validate(self, data):
        if not CourseToLibraryImport.get_ready_by_uuid(data['import_id']):
            raise serializers.ValidationError({'import_id': 'Invalid import ID.'})
        return data
