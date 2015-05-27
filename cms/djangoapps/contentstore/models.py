"""
Models for contentstore
"""
# pylint: disable=no-member

from django.db.models.fields import TextField

from config_models.models import ConfigurationModel


class VideoUploadConfig(ConfigurationModel):
    """Configuration for the video upload feature."""
    profile_whitelist = TextField(
        blank=True,
        help_text="A comma-separated list of names of profiles to include in video encoding downloads."
    )

    @classmethod
    def get_profile_whitelist(cls):
        """Get the list of profiles to include in the encoding download"""
        return [profile for profile in cls.current().profile_whitelist.split(",") if profile]


class PushNotificationConfig(ConfigurationModel):
    """Configuration for mobile push notifications."""
