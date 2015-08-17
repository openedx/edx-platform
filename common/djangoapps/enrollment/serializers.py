"""
Serializers for all Course Enrollment related return objects.

"""
import logging

from rest_framework import serializers
from student.models import CourseEnrollment
from course_modes.models import CourseMode


log = logging.getLogger(__name__)


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

    def to_native(self, course, **kwargs):
        course_id = unicode(course.id)
        course_modes = ModeSerializer(
            CourseMode.modes_for_course(course.id, kwargs.get('include_expired', False), only_selectable=False)
        ).data  # pylint: disable=no-member

        return {
            "course_id": course_id,
            "enrollment_start": course.enrollment_start,
            "enrollment_end": course.enrollment_end,
            "course_start": course.start,
            "course_end": course.end,
            "invite_only": course.invitation_only,
            "course_modes": course_modes,
        }


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializes CourseEnrollment models

    Aggregates all data from the Course Enrollment table, and pulls in the serialization for
    the Course Descriptor and course modes, to give a complete representation of course enrollment.

    """
    course_details = serializers.SerializerMethodField('get_course_details')
    user = serializers.SerializerMethodField('get_username')

    @property
    def data(self):
        serialized_data = super(CourseEnrollmentSerializer, self).data

        # filter the results with empty courses 'course_details'
        if isinstance(serialized_data, dict):
            if serialized_data.get('course_details') is None:
                return None

            return serialized_data

        return [enrollment for enrollment in serialized_data if enrollment.get('course_details')]

    def get_course_details(self, model):
        if model.course is None:
            msg = u"Course '{0}' does not exist (maybe deleted), in which User (user_id: '{1}') is enrolled.".format(
                model.course_id,
                model.user.id
            )
            log.warning(msg)
            return None

        field = CourseField()
        return field.to_native(model.course)

    def get_username(self, model):
        """Retrieves the username from the associated model."""
        return model.username

    class Meta(object):  # pylint: disable=missing-docstring
        model = CourseEnrollment
        fields = ('created', 'mode', 'is_active', 'course_details', 'user')
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
    sku = serializers.CharField()
