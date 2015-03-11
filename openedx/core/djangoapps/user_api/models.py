from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from model_utils.models import TimeStampedModel

from xmodule_django.models import CourseKeyField

from .api.user import UserApiRequestError

# Currently, the "student" app is responsible for
# accounts, profiles, enrollments, and the student dashboard.
# We are trying to move some of this functionality into separate apps,
# but currently the rest of the system assumes that "student" defines
# certain models.  For now we will leave the models in "student" and
# create an alias in "user_api".
from student.models import UserProfile, Registration, PendingEmailChange  # pylint: disable=unused-import


class PreferenceRequestError(UserApiRequestError):
    """There was a problem with a preference request."""
    pass


class PreferenceNotFound(PreferenceRequestError):
    """The desired user preference was not found."""
    pass


class PreferenceValidationError(PreferenceRequestError):
    """
    Validation issues were found with the supplied data. More detailed information is present
    in preference_errors, a dict with specific information about each preference that failed
    validation. For each preference, there will be at least a developer_message describing
    the validation issue, and possibly also a user_message.
    """
    def __init__(self, preference_errors):
        self.preference_errors = preference_errors


class PreferenceUpdateError(PreferenceRequestError):
    """
    An update to the account failed. More detailed information is present in developer_message,
    and depending on the type of error encountered, there may also be a non-null user_message field.
    """
    def __init__(self, developer_message, user_message=None):
        self.developer_message = developer_message
        self.user_message = user_message


class UserPreference(models.Model):
    """A user's preference, stored as generic text to be processed by client"""
    KEY_REGEX = r"[-_a-zA-Z0-9]+"
    user = models.ForeignKey(User, db_index=True, related_name="preferences")
    key = models.CharField(max_length=255, db_index=True, validators=[RegexValidator(KEY_REGEX)])
    value = models.TextField()

    class Meta:  # pylint: disable=missing-docstring
        unique_together = ("user", "key")

    @classmethod
    def set_preference(cls, user, preference_key, preference_value):
        """Sets the user preference for a given key, creating it if it doesn't exist.

        Arguments:
            user (User): The user whose preference should be set.
            preference_key (string): The key for the user preference.
            preference_value (string): The value to be stored.
            save (boolean): If true then save the model (defaults to True).

        Raises:
            ValidationError: the update was rejected because it was invalid
        """
        user_preference, _ = cls.objects.get_or_create(user=user, key=preference_key)
        user_preference.value = preference_value
        user_preference.full_clean()
        user_preference.save()

    @classmethod
    def validate_preference(cls, user, preference_key, preference_value):
        """Validates the combination of preference key and value.

        Arguments:
            user (User): The user whose preference should be validated.
            preference_key (string): The key for the user preference.
            preference_value (string): The value to be stored.

        Raises:
            ValidationError: returned if the key and/or value is invalid.
        """
        user_preference, _ = cls.objects.get_or_create(user=user, key=preference_key)
        old_value = user_preference.value
        user_preference.value = preference_value
        try:
            user_preference.full_clean()
        finally:
            user_preference.value = old_value

    @classmethod
    def get_preference(cls, user, preference_key, default=None):
        """Gets the user preference value for a given key

        Arguments:
            user (User): The user whose preference should be set.
            preference_key (string): The key for the user preference.
            default (object): The default value to return if the preference is not set.

        Returns:
            The user preference value, or the specified default if one is not set.
        """
        try:
            user_preference = cls.objects.get(user=user, key=preference_key)
            return user_preference.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def delete_preference(cls, user, preference_key):
        """Deletes the user preference value for a given key

        Arguments:
            user (User): The user whose preference should be set.
            preference_key (string): The key for the user preference.

        Raises:
            PreferenceNotFound: No preference was found with the given key.
        """
        try:
            user_preference = cls.objects.get(user=user, key=preference_key)
        except cls.DoesNotExist:
            raise PreferenceNotFound()
        user_preference.delete()


class UserCourseTag(models.Model):
    """
    Per-course user tags, to be used by various things that want to store tags about
    the user.  Added initially to store assignment to experimental groups.
    """
    user = models.ForeignKey(User, db_index=True, related_name="+")
    key = models.CharField(max_length=255, db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True)
    value = models.TextField()

    class Meta:  # pylint: disable=missing-docstring
        unique_together = ("user", "course_id", "key")


class UserOrgTag(TimeStampedModel):
    """ Per-Organization user tags.

    Allows settings to be configured at an organization level.

    """
    user = models.ForeignKey(User, db_index=True, related_name="+")
    key = models.CharField(max_length=255, db_index=True)
    org = models.CharField(max_length=255, db_index=True)
    value = models.TextField()

    class Meta:
        """ Meta class for defining unique constraints. """
        unique_together = ("user", "org", "key")
