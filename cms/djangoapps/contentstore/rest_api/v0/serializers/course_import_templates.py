from rest_framework import serializers

from cms.djangoapps.contentstore.models import CourseImportTemplate


class CourseImportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseImportTemplate
        fields = '__all__'
        read_only_fields = ['added_by']

    thumbnail = serializers.ImageField(required=False, allow_null=True)
