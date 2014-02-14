from django.contrib.auth.models import User
from django.db import models

# this is the UserPreference key for the user's preferred language
LANGUAGE_KEY = 'pref-lang'


class UserPreference(models.Model):
    """A user's preference, stored as generic text to be processed by client"""
    user = models.ForeignKey(User, db_index=True, related_name="+")
    key = models.CharField(max_length=255, db_index=True)
    value = models.TextField()

    class Meta:
        unique_together = ("user", "key")

    @classmethod
    def set_preference(cls, user, preference_key, preference_value):
        """
        Sets the user preference for a given key
        """
        user_pref, _ = cls.objects.get_or_create(user=user, key=preference_key)
        user_pref.value = preference_value
        user_pref.save()

    @classmethod
    def get_preference(cls, user, preference_key, default=None):
        """
        Gets the user preference value for a given key

        Returns the given default if there isn't a preference for the given key
        """

        try:
            user_pref = cls.objects.get(user=user, key=preference_key)
            return user_pref.value
        except cls.DoesNotExist:
            return default
