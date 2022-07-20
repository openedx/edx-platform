from unittest.mock import Base # To Import
from rest_framework import serializers # To Import
from common.djangoapps.student.models import DocumentStorage ,Announcement # To Import


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentStorage
        
        exclude= ('created_by', 'added_on', 'updated_on')


class AnnouncementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Announcement
        fields = ('id', 'content', 'announcement_bases', 'announcement_for')

    
    def validate(self, data):
        announcement_bases = data.get('announcement_bases')
        announcement_for = data.get('announcement_for')
        if announcement_bases != "all":
            if type(announcement_for) is list and announcement_for !=[]:
                if announcement_bases == "student":
                    for announcement in announcement_for:
                        if not announcement.isdigit():
                            raise serializers.ValidationError({"announcement_for":'Should be list of student id'})
            else:
                raise serializers.ValidationError({"announcement_for":'Sould be list which is not empty'})
        return data