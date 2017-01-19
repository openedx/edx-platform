from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import serializers


class StringListField(serializers.ListField):
    def to_internal_value(self, data):
        return data.split(',')

class BulkEnrollmentSerializer(serializers.Serializer):
    identifiers = serializers.CharField(required=True)
    courses = StringListField(required=True)
    action = serializers.ChoiceField(
        choices=(
            ('enroll', 'enroll'),
            ('unenroll', 'unenroll')
        ),
        required=True
    )
    auto_enroll = serializers.BooleanField(default=False)
    email_students = serializers.BooleanField(default=False)

    def validate_courses(self, value):
        """
        Check that each course key in list is valid.
        """
        course_keys = value
        for course in course_keys:
            try:
                CourseKey.from_string(course)
            except InvalidKeyError:
                raise serializers.ValidationError("Course key not valid: {}".format(course))
        return value
