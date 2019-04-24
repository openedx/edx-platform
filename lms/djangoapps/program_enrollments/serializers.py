"""
Serializers for program_enrollments
"""
from rest_framework import serializers


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


class ProgramCourseEnrollmentRequestSerializer(serializers.Serializer, InvalidStatusMixin):  # pylint: disable=abstract-method
    """
    Serializer for request to create a ProgramCourseEnrollment
    """
    STATUS_CHOICES = ['active', 'inactive']

    student_key = serializers.CharField(allow_blank=False)
    status = serializers.ChoiceField(allow_blank=False, choices=STATUS_CHOICES)
