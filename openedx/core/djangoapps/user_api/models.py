from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import pre_delete, post_delete, pre_save, post_save
from django.dispatch import receiver
from model_utils.models import TimeStampedModel

from util.model_utils import get_changed_fields_dict, emit_setting_changed_event
from xmodule_django.models import CourseKeyField

# Currently, the "student" app is responsible for
# accounts, profiles, enrollments, and the student dashboard.
# We are trying to move some of this functionality into separate apps,
# but currently the rest of the system assumes that "student" defines
# certain models.  For now we will leave the models in "student" and
# create an alias in "user_api".
from student.models import UserProfile, Registration, PendingEmailChange  # pylint: disable=unused-import


class UserPreference(models.Model):
    """A user's preference, stored as generic text to be processed by client"""
    KEY_REGEX = r"[-_a-zA-Z0-9]+"
    user = models.ForeignKey(User, db_index=True, related_name="preferences")
    key = models.CharField(max_length=255, db_index=True, validators=[RegexValidator(KEY_REGEX)])
    value = models.TextField()

    class Meta:  # pylint: disable=missing-docstring
        unique_together = ("user", "key")

    @classmethod
    def get_value(cls, user, preference_key):
        """Gets the user preference value for a given key.

        Note:
            This method provides no authorization of access to the user preference.
            Consider using user_api.preferences.api.get_user_preference instead if
            this is part of a REST API request.

        Arguments:
            user (User): The user whose preference should be set.
            preference_key (str): The key for the user preference.

        Returns:
            The user preference value, or None if one is not set.
        """
        try:
            user_preference = cls.objects.get(user=user, key=preference_key)
            return user_preference.value
        except cls.DoesNotExist:
            return None


@receiver(pre_save, sender=UserPreference)
def pre_save_callback(sender, **kwargs):
    """
    Event changes to user preferences.
    """
    user_preference = kwargs["instance"]
    user_preference._old_value = get_changed_fields_dict(user_preference, sender).get("value", None)


@receiver(post_save, sender=UserPreference)
def post_save_callback(sender, **kwargs):
    """
    Event changes to user preferences.
    """
    user_preference = kwargs["instance"]
    emit_setting_changed_event(
        user_preference.user, sender._meta.db_table, user_preference.key,
        user_preference._old_value, user_preference.value
    )
    user_preference._old_value = None


@receiver(post_delete, sender=UserPreference)
def post_delete_callback(sender, **kwargs):
    """
    Event changes to user preferences.
    """
    user_preference = kwargs["instance"]
    emit_setting_changed_event(
        user_preference.user, sender._meta.db_table, user_preference.key, user_preference.value, None
    )


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
