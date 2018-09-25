
from student.models import CourseEnrollment

from rest_framework import serializers


class CourseEnrollmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseEnrollment
        fields = '__all__'#('created', )

    def to_representation(self, instance):
        representation = super(CourseEnrollmentSerializer, self).to_representation(instance)
        print(type(representation))
        representation['course'] =  "Course: {}".format(representation['course'])
        print(representation.keys())
        return representation