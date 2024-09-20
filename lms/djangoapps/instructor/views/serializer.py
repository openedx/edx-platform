""" Instructor apis serializers. """

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from rest_framework import serializers
from .tools import get_student_from_identifier

from lms.djangoapps.instructor.access import ROLES


class RoleNameSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer that describes the response of the problem response report generation API.
    """

    rolename = serializers.CharField(help_text=_("Role name"))

    def validate_rolename(self, value):
        """
        Check that the rolename is valid.
        """
        if value not in ROLES:
            raise ValidationError(_("Invalid role name."))
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class UniqueStudentIdentifierSerializer(serializers.Serializer):
    """
    Serializer for identifying unique_student.
    """
    unique_student_identifier = serializers.CharField(
        max_length=255,
        help_text="Email or username of user to change access"
    )

    def validate_unique_student_identifier(self, value):
        """
        Validate that the unique_student_identifier corresponds to an existing user.
        """
        try:
            user = get_student_from_identifier(value)
        except User.DoesNotExist:
            return None

        return user


class AccessSerializer(UniqueStudentIdentifierSerializer):
    """
    Serializer for managing user access changes.
    This serializer validates and processes the data required to modify
    user access within a system.
    """
    rolename = serializers.CharField(
        help_text="Role name to assign to the user"
    )
    action = serializers.ChoiceField(
        choices=['allow', 'revoke'],
        help_text="Action to perform on the user's access"
    )


class ListInstructorTaskInputSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for handling the input data for the problem response report generation API.

Attributes:
    unique_student_identifier (str): The email or username of the student.
                                      This field is optional, but if provided, the `problem_location_str`
                                      must also be provided.
    problem_location_str (str): The string representing the location of the problem within the course.
                                This field is optional, unless `unique_student_identifier` is provided.
    """
    unique_student_identifier = serializers.CharField(
        max_length=255,
        help_text="Email or username of student",
        required=False
    )
    problem_location_str = serializers.CharField(
        help_text="Problem location",
        required=False
    )

    def validate(self, data):
        """
        Validate the data to ensure that if unique_student_identifier is provided,
        problem_location_str must also be provided.
        """
        unique_student_identifier = data.get('unique_student_identifier')
        problem_location_str = data.get('problem_location_str')

        if unique_student_identifier and not problem_location_str:
            raise serializers.ValidationError(
                "unique_student_identifier must accompany problem_location_str"
            )

        return data


class ShowStudentExtensionSerializer(serializers.Serializer):
    """
    Serializer for validating and processing the student identifier.
    """
    student = serializers.CharField(write_only=True, required=True)

    def validate_student(self, value):
        """
        Validate that the student corresponds to an existing user.
        """
        try:
            user = get_student_from_identifier(value)
        except User.DoesNotExist:
            return None

        return user


class StudentAttemptsSerializer(serializers.Serializer):
    """
    Serializer for resetting a students attempts counter or starts a task to reset all students
    attempts counters.
    """
    problem_to_reset = serializers.CharField(
        help_text="The identifier or description of the problem that needs to be reset."
    )

    # following are optional params.
    unique_student_identifier = serializers.CharField(
        help_text="Email or username of student.", required=False
    )
    all_students = serializers.CharField(required=False)
    delete_module = serializers.CharField(required=False)

    def validate_all_students(self, value):
        """
        converts the all_student params value to bool.
        """
        return self.verify_bool(value)

    def validate_delete_module(self, value):
        """
        converts the all_student params value.
        """
        return self.verify_bool(value)

    def validate_unique_student_identifier(self, value):
        """
        Validate that the student corresponds to an existing user.
        """
        try:
            user = get_student_from_identifier(value)
        except User.DoesNotExist:
            return None

        return user

    def verify_bool(self, value):
        """
        Returns the value of the boolean parameter with the given
        name in the POST request. Handles translation from string
        values to boolean values.
        """
        if value is not None:
            return value in ['true', 'True', True]

        return False


class SendEmailSerializer(serializers.Serializer):
    """
    Serializer for sending an email with optional scheduling.

    Fields:
        send_to (str): The email address of the recipient. This field is required.
        subject (str): The subject line of the email. This field is required.
        message (str): The body of the email. This field is required.
        schedule (str, optional):
        An optional field to specify when the email should be sent.
        If provided, this should be a string that can be parsed into a
        datetime format or some other scheduling logic.
    """
    send_to = serializers.CharField(write_only=True, required=True)

    # set max length as per model field.
    subject = serializers.CharField(max_length=128, write_only=True, required=True)
    message = serializers.CharField(required=True)
    schedule = serializers.CharField(required=False)


class BlockDueDateSerializer(serializers.Serializer):
    """
    Serializer for handling block due date updates for a specific student.
    Fields:
        url (str): The URL related to the block that needs the due date update.
        due_datetime (str): The new due date and time for the block.
        student (str): The email or username of the student whose access is being modified.
        reason (str): Reason why updating this.
    """
    url = serializers.CharField()
    due_datetime = serializers.CharField()
    student = serializers.CharField(
        max_length=255,
        help_text="Email or username of user to change access"
    )
    reason = serializers.CharField(required=False)

    def validate_student(self, value):
        """
        Validate that the student corresponds to an existing user.
        """
        try:
            user = get_student_from_identifier(value)
        except User.DoesNotExist:
            return None

        return user

    def __init__(self, *args, **kwargs):
        # Get context to check if `due_datetime` should be optional
        disable_due_datetime = kwargs.get('context', {}).get('disable_due_datetime', False)
        super().__init__(*args, **kwargs)
        if disable_due_datetime:
            self.fields['due_datetime'].required = False
