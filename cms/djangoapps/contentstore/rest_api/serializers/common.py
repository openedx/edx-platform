"""
Common API Serializers
"""

from rest_framework import serializers

from openedx.core.lib.api.serializers import CourseKeyField


class CourseCommonSerializer(serializers.Serializer):
    """Serializer for course renders"""
    course_key = CourseKeyField()
    display_name = serializers.CharField()
    lms_link = serializers.CharField()
    number = serializers.CharField()
    org = serializers.CharField()
    rerun_link = serializers.CharField()
    run = serializers.CharField()
    url = serializers.CharField()


class StrictSerializer(serializers.Serializer):
    """
    Serializers that validates strong parameters, i.e. that no extra fields are passed in.
    The serializer inheriting from this may throw a ValidationError and can be called in a try/catch
    block that will return a 400 response on ValidationError.
    """
    def to_internal_value(self, data):
        """
        raise validation error if there are any unexpected fields.
        """
        # Transform and validate the expected fields
        ret = super().to_internal_value(data)

        # Get the list of valid fields from the serializer
        valid_fields = set(self.fields.keys())

        # Check for unexpected fields
        extra_fields = set(data.keys()) - valid_fields
        if extra_fields:
            # Check if these unexpected fields are due to nested serializers
            for field_name in list(extra_fields):
                if isinstance(self.fields.get(field_name), serializers.BaseSerializer):
                    extra_fields.remove(field_name)

            # If there are still unexpected fields left, raise an error
            if extra_fields:
                raise serializers.ValidationError(
                    {field: ["This field is not expected."] for field in extra_fields}
                )

        return ret


class ProctoringErrorModelSerializer(serializers.Serializer):
    """
    Serializer for proctoring error model item.
    """
    deprecated = serializers.BooleanField()
    display_name = serializers.CharField()
    help = serializers.CharField()
    hide_on_enabled_publisher = serializers.BooleanField()
    value = serializers.CharField()


class ProctoringErrorListSerializer(serializers.Serializer):
    """
    Serializer for proctoring error list.
    """
    key = serializers.CharField()
    message = serializers.CharField()
    model = ProctoringErrorModelSerializer()
