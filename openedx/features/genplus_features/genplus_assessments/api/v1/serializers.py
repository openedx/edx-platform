from rest_framework import serializers

from openedx.features.genplus_features.genplus.models import Student
from openedx.features.genplus_features.genplus.models import Class
from openedx.features.genplus_features.genplus_learning.models import (
    ClassLesson,
    ClassUnit
)


class ClassLessonSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClassLesson
        fields = ('id', 'display_name', 'lms_url', 'usage_key')

class ClassUnitSerializer(serializers.ModelSerializer):
    class_lessons = ClassLessonSerializer(many=True, read_only=True)
    display_name = serializers.CharField(source="unit.display_name")

    class Meta:
        model = ClassUnit
        fields = ('id', 'display_name', 'course_key' ,'class_lessons')

class ClassStudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    user_id = serializers.CharField(source='user.id')

    class Meta:
        model = Student
        fields = ('id', 'user_id', 'username')


class ClassSerializer(serializers.ModelSerializer):
    students = ClassStudentSerializer(many=True, read_only=True)
    class_units = ClassUnitSerializer(many=True, read_only=True)
    
    class Meta:
        model = Class
        fields = ('group_id', 'name', 'students', 'class_units')
