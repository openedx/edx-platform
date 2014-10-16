"""
Serializers for all Course Enrollment related return objects.

"""
from rest_framework import serializers
from student.models import CourseEnrollment


class CourseField(serializers.RelatedField):
    """Custom field to wrap a CourseDescriptor object. Read-only."""

    def to_native(self, course):
        course_id = unicode(course.id)

        return {
            "course_id": course_id,
            "enrollment_start": course.enrollment_start,
            "enrollment_end": course.enrollment_end,
            "invite_only": course.invite_only
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


class CourseEnrollmentInfoSerializer(serializers.BaseSerializer):
    """Serializes the the course enrollment information."""
    pass


class CourseModeSerializer(serializers.ModelSerializer):
    """Serializes the Course Modes models."""
    pass