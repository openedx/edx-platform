""" Credit API Serializers """

from rest_framework import serializers

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from openedx.core.djangoapps.credit.models import CreditCourse, CreditProvider, CreditEligibility


class CourseKeyField(serializers.Field):
    """
    Serializer field for a model CourseKey field.
    """

    def to_representation(self, data):
        """Convert a course key to unicode. """
        return unicode(data)

    def to_internal_value(self, data):
        """Convert unicode to a course key. """
        try:
            return CourseKey.from_string(data)
        except InvalidKeyError as ex:
            raise serializers.ValidationError("Invalid course key: {msg}".format(msg=ex.msg))


class CreditCourseSerializer(serializers.ModelSerializer):
    """ CreditCourse Serializer """

    course_key = CourseKeyField()

    class Meta(object):  # pylint: disable=missing-docstring
        model = CreditCourse
        exclude = ('id',)


class CreditProviderSerializer(serializers.ModelSerializer):
    """ CreditProvider Serializer """

    class Meta(object):  # pylint: disable=missing-docstring
        model = CreditProvider
        exclude = ('id', 'eligibility_email_message', 'receipt_email_message')


class CreditEligibilitySerializer(serializers.ModelSerializer):
    """ CreditEligibility Serializer """

    course_key = serializers.CharField(source='course.course_key')

    class Meta(object):  # pylint: disable=missing-docstring
        model = CreditEligibility
        fields = ('course_key', 'deadline')
