"""
API Serializers
"""
from __future__ import absolute_import

from rest_framework import serializers
from six import text_type

from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment


# pylint: disable=abstract-method
class ProgramEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Program Enrollments
    """

    class Meta(object):
        model = ProgramEnrollment
        fields = ('user', 'external_user_key', 'program_uuid', 'curriculum_uuid', 'status')
        validators = []

    def validate(self, attrs):
        """ This modifies self.instance in the case of updates """
        if not self.instance:
            enrollment = ProgramEnrollment(**attrs)
            enrollment.full_clean()
        else:
            for key, value in attrs.items():
                setattr(self.instance, key, value)
            self.instance.full_clean()

        return attrs

    def create(self, validated_data):
        return ProgramEnrollment.objects.create(**validated_data)


class ProgramEnrollmentListSerializer(serializers.Serializer):
    """
    Serializer for listing enrollments in a program.
    """
    student_key = serializers.CharField(source='external_user_key')
    status = serializers.CharField()
    account_exists = serializers.SerializerMethodField()
    curriculum_uuid = serializers.UUIDField()

    class Meta(object):
        model = ProgramEnrollment

    def get_account_exists(self, obj):
        return bool(obj.user)


class InvalidStatusMixin(object):
    """
    Mixin to provide has_invalid_status method
    """
    def has_invalid_status(self):
        """
        Returns whether or not this serializer has an invalid error choice on the "status" field
        """
        try:
            for status_error in self.errors['status']:
                if status_error.code == 'invalid_choice':
                    return True
        except KeyError:
            pass
        return False


# pylint: disable=abstract-method
class ProgramCourseEnrollmentRequestSerializer(serializers.Serializer, InvalidStatusMixin):
    """
    Serializer for request to create a ProgramCourseEnrollment
    """
    STATUS_CHOICES = ['active', 'inactive']

    student_key = serializers.CharField(allow_blank=False)
    status = serializers.ChoiceField(allow_blank=False, choices=STATUS_CHOICES)


class ProgramCourseEnrollmentListSerializer(serializers.Serializer):
    """
    Serializer for listing course enrollments in a program.
    """
    student_key = serializers.SerializerMethodField()
    status = serializers.CharField()
    account_exists = serializers.SerializerMethodField()
    curriculum_uuid = serializers.SerializerMethodField()

    class Meta(object):
        model = ProgramCourseEnrollment

    def get_student_key(self, obj):
        return obj.program_enrollment.external_user_key

    def get_account_exists(self, obj):
        return bool(obj.program_enrollment.user)

    def get_curriculum_uuid(self, obj):
        return text_type(obj.program_enrollment.curriculum_uuid)
