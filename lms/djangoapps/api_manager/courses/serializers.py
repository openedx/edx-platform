""" Django REST Framework Serializers """

from api_manager.models import CourseModuleCompletion
from rest_framework import serializers


class CourseModuleCompletionSerializer(serializers.ModelSerializer):
    """ Serializer for CourseModuleCompletion model interactions """
    user_id = serializers.Field(source='user.id')

    class Meta:
        """ Serializer/field specification """
        model = CourseModuleCompletion
        fields = ('id', 'user_id', 'course_id', 'content_id', 'created', 'modified')
        read_only = ('id', 'created')
