"""
Serializers for the Course to Library Import API.
"""

from rest_framework import serializers

from cms.djangoapps.import_from_modulestore.validators import validate_composition_level


class ImportBlocksSerializer(serializers.Serializer):
    """
    Serializer for the import blocks API.
    """

    usage_ids = serializers.ListField(
        child=serializers.CharField(),
        required=True,
    )
    import_uuid = serializers.CharField(required=True)
    composition_level = serializers.CharField(
        required=True,
        validators=[validate_composition_level],
    )
    override = serializers.BooleanField(default=False, required=False)


class CourseToLibraryImportSerializer(serializers.Serializer):
    """
    Serializer for the course to library import creation API.
    """

    course_ids = serializers.ListField()
    status = serializers.CharField(allow_blank=True, required=False)
    library_key = serializers.CharField(allow_blank=True, required=False)
    uuid = serializers.CharField(allow_blank=True, required=False)
