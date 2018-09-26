

import logging

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment

from rest_framework import serializers


class CourseEnrollmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = CourseEnrollment
        fields = '__all__'#('created', )

    def to_representation(self, instance):
        representation = super(CourseEnrollmentSerializer, self).to_representation(instance)
        representation['course'] =  "Course: {}".format(representation['course'])
        representation['course_end'] = instance.course.end
        return representation