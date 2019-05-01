"""
API Serializers
"""
from rest_framework import serializers

from lms.djangoapps.program_enrollments.models import ProgramEnrollment


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
        enrollment = ProgramEnrollment(**attrs)
        enrollment.full_clean()
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
        Returns whether or not this serializer has an invlaid error choice on the "status" field
        """
        invalid_status = 'status' in self.errors
        return invalid_status and self.errors['status'][0].code == 'invalid_choice'


# pylint: disable=abstract-method
class ProgramCourseEnrollmentRequestSerializer(serializers.Serializer, InvalidStatusMixin):
    """
    Serializer for request to create a ProgramCourseEnrollment
    """
    STATUS_CHOICES = ['active', 'inactive']

    student_key = serializers.CharField(allow_blank=False)
    status = serializers.ChoiceField(allow_blank=False, choices=STATUS_CHOICES)
