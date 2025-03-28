"""
Serializers for the Course to Library Import API.
"""

from rest_framework import serializers

from cms.djangoapps.course_to_library_import import api
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


class CourseToLibraryImportSerializer(serializers.ModelSerializer):
    """
    Serializer for CourseToLibraryImport model.
    """

    course_ids = serializers.ListField()
    status = serializers.CharField(allow_blank=True, required=False)
    library_key = serializers.CharField(allow_blank=True, required=False)
    uuid = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = CourseToLibraryImport
        fields = ('course_ids', 'status', 'library_key', 'uuid')

    def create(self, validated_data):
        """
        Run the import creation logic.
        Creates a new CourseToLibraryImport instance and related data such as StagedContent.
        """
        user = getattr(self.context.get('request'), 'user', None)
        course_to_library_import = api.create_import(
            validated_data['course_ids'],
            getattr(user, 'pk', None),
            self.context.get('content_library_id'),
        )
        return course_to_library_import

    def to_representation(self, instance):
        """
        Converts a string with course IDs into a list of strings with course IDs.
        """
        representation = super().to_representation(instance)
        representation['course_ids'] = ''.join(representation['course_ids']).split()
        return representation
