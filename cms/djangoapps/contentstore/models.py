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
    status_whitelist = TextField(
        blank=True,
        help_text=(
            "A comma-separated list of Studio status values;" +
            " only videos with these status values will be included in video encoding downloads."
        )
    )

    @classmethod
    def get_profile_whitelist(cls):
        """Get the list of profiles to include in the encoding download"""
        return [profile for profile in cls.current().profile_whitelist.split(",") if profile]

    @classmethod
    def get_status_whitelist(cls):
        """
        Get the list of status values to include files for in the encoding
        download
        """
        return [status for status in cls.current().status_whitelist.split(",") if status]
