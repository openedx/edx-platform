"""
Models for contentstore
"""


from config_models.models import ConfigurationModel
from django.db.models.fields import IntegerField, TextField


class VideoUploadConfig(ConfigurationModel):
    """
    Configuration for the video upload feature.

    .. no_pii:
    """
    profile_whitelist = TextField(
        blank=True,
        help_text="A comma-separated list of names of profiles to include in video encoding downloads."
    )

    @classmethod
    def get_profile_whitelist(cls):
        """Get the list of profiles to include in the encoding download"""
        return [profile for profile in cls.current().profile_whitelist.split(",") if profile]


class BackfillCourseTabsConfig(ConfigurationModel):
    """
    Manages configuration for a run of the backfill_course_tabs management command.

    .. no_pii:
    """

    class Meta:
        verbose_name = 'Arguments for backfill_course_tabs'
        verbose_name_plural = 'Arguments for backfill_course_tabs'

    start_index = IntegerField(
        help_text='Index of first course to start backfilling (in an alphabetically sorted list of courses)',
        default=0,
    )
    count = IntegerField(
        help_text='How many courses to backfill in this run (or zero for all courses)',
        default=0,
    )
