"""
Serializers for all Course Enrollment related return objects.

"""
from rest_framework import serializers
from student.models import CourseEnrollment
from course_modes.models import CourseMode


class StringListField(serializers.CharField):
    """Custom Serializer for turning a comma delimited string into a list.

    This field is designed to take a string such as "1,2,3" and turn it into an actual list
    [1,2,3]

    """
    def field_to_native(self, obj, field_name):
        """
        Serialize the object's class name.
        """
        if not obj.suggested_prices:
            return []

        items = obj.suggested_prices.split(',')
        return [int(item) for item in items]


class CourseField(serializers.RelatedField):
    """Read-Only representation of course enrollment information.

    Aggregates course information from the CourseDescriptor as well as the Course Modes configured
    for enrolling in the course.

    """

    def to_native(self, course):
        course_id = unicode(course.id)
        course_modes = ModeSerializer(CourseMode.modes_for_course(course.id)).data  # pylint: disable=no-member

        return {
            "course_id": course_id,
            "enrollment_start": course.enrollment_start,
            "enrollment_end": course.enrollment_end,
            "invite_only": course.invitation_only,
            "course_modes": course_modes,
        }


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializes CourseEnrollment models

    Aggregates all data from the Course Enrollment table, and pulls in the serialization for
    the Course Descriptor and course modes, to give a complete representation of course enrollment.

    """
    course = CourseField()

    class Meta:  # pylint: disable=C0111
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course')
        lookup_field = 'username'


class ModeSerializer(serializers.Serializer):
    """Serializes a course's 'Mode' tuples

    Returns a serialized representation of the modes available for course enrollment. The course
    modes models are designed to return a tuple instead of the model object itself. This serializer
    does not handle the model object itself, but the tuple.

    """
    slug = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    min_price = serializers.IntegerField()
    suggested_prices = StringListField(max_length=255)
    currency = serializers.CharField(max_length=8)
    expiration_datetime = serializers.DateTimeField()
    description = serializers.CharField()
