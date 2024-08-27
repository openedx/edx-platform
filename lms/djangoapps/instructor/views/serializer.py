""" Instructor apis serializers. """

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from rest_framework import serializers

from lms.djangoapps.instructor.access import ROLES
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_GROUP_MODERATOR,
    FORUM_ROLE_MODERATOR,
    Role
)
from lms.djangoapps.discussion.django_comment_client.utils import (
    get_group_id_for_user,
    get_group_name
)

from .tools import get_student_from_identifier


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


class AccessSerializer(serializers.Serializer):
    """
    Serializer for managing user access changes.
    This serializer validates and processes the data required to modify
    user access within a system.
    """
    unique_student_identifier = serializers.CharField(
        max_length=255,
        help_text="Email or username of user to change access"
    )
    rolename = serializers.CharField(
        help_text="Role name to assign to the user"
    )
    action = serializers.ChoiceField(
        choices=['allow', 'revoke'],
        help_text="Action to perform on the user's access"
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


class ForumRoleNameSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for forum rolename.
    """

    rolename = serializers.CharField(help_text=_("Role name"))
    users = serializers.SerializerMethodField()

    def validate_rolename(self, value):
        """
        Check that the rolename is valid.
        """
        if value not in [
            FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_GROUP_MODERATOR, FORUM_ROLE_MODERATOR
        ]:
            raise ValidationError(_("Invalid role name."))
        return value

    def get_users(self, obj):
        """
        Retrieve a list of users associated with the specified role and course.

        Args:
            obj (dict): A dictionary containing the 'rolename' for which to retrieve users.
                        This dictionary is the data passed to the serializer.

        Returns:
            list: A list of dictionaries, each representing a user associated with the specified role.
                  Each user dictionary contains 'username', 'email', 'first_name', 'last_name', and 'group_name'.
                  If no users are found, an empty list is returned.

        """
        course_id = self.context.get('course_id')
        rolename = obj['rolename']
        try:
            role = Role.objects.get(name=rolename, course_id=course_id)
            users = role.users.all().order_by('username')
        except Role.DoesNotExist:
            users = []

        return [extract_user_info(user, self.context.get('course_discussion_settings')) for user in users]


def extract_user_info(user, course_discussion_settings):
    """ utility method to convert user into dict for JSON rendering. """
    group_id = get_group_id_for_user(user, course_discussion_settings)
    group_name = get_group_name(group_id, course_discussion_settings)

    return {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'group_name': group_name,
    }

  
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
