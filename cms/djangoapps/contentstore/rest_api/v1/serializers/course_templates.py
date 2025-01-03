from rest_framework import serializers

class CourseMetadataSerializer(serializers.Serializer):
    course_id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    thumbnail = serializers.URLField()
    active = serializers.BooleanField()

class CourseSerializer(serializers.Serializer):
    courses_name = serializers.CharField()
    zip_url = serializers.URLField()
    metadata = CourseMetadataSerializer()
