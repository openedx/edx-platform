from unittest.mock import Base # To Import
from rest_framework import serializers # To Import
from common.djangoapps.student.models import DocumentStorage # To Import


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentStorage
        
        exclude= ('created_by', 'added_on', 'updated_on')
