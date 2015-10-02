""" Enrollment API v2 serializers. """

from rest_framework import serializers

from student.models import CourseEnrollment


class CourseEnrollmentSerializer(serializers.ModelSerializer):  # pylint: disable=missing-docstring
    class Meta(object):
        model = CourseEnrollment
