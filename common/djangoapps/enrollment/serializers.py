"""
Serializers for all Course Enrollment related return objects.

"""
from rest_framework import serializers
from student.models import CourseEnrollment
from course_modes.models import CourseMode


class CourseField(serializers.RelatedField):
    """Custom field to wrap a CourseDescriptor object. Read-only."""

    def to_native(self, course):
        course_id = unicode(course.id)
        course_modes = ModeSerializer(CourseMode.modes_for_course(course.id)).data

        return {
            "course_id": course_id,
            "enrollment_start": course.enrollment_start,
            "enrollment_end": course.enrollment_end,
            "invite_only": course.invitation_only,
            "course_modes": course_modes,
        }


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializes CourseEnrollment models

    """
    course = CourseField()

    class Meta:  # pylint: disable=C0111
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course')
        lookup_field = 'username'


class ModeSerializer(serializers.Serializer):
    """Serializes a course's 'Mode' tuples"""
    slug = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    min_price = serializers.IntegerField()
    suggested_prices = serializers.CharField(max_length=255)
    currency = serializers.CharField(max_length=8)
    expiration_datetime = serializers.DateTimeField()
    description = serializers.CharField()
