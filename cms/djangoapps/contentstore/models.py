"""
Models for contentstore
"""


from config_models.models import ConfigurationModel
from django.db.models.fields import IntegerField, TextField,CharField
from django.db import models


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


class CleanStaleCertificateAvailabilityDatesConfig(ConfigurationModel):
    """
    Manages configuration for a run of the `clean_stale_certificate_availability_dates` management command.

    .. no_pii:
    """
    class Meta:
        app_label = "contentstore"
        verbose_name = "Arguments for 'clean_stale_certificate_availability_dates'"
        verbose_name_plural = "Arguments for 'clean_stale_certificate_availability_dates'"

    arguments = TextField(
        blank=True,
        help_text=(
            "A space seperated collection of arguments to be used when running the "
            "`clean_stale_certificate_available_dates` management command.' See the management command for options."
        )
    )

# model course unit time

class CourseUnitTime (models.Model):
    block_id =  CharField(max_length=255)
    course_id = CharField(max_length=255)
    display_name = CharField(max_length=255)
    total = IntegerField(default=0)

    def __str__(self):
        return self.block_id
    
    @classmethod
    def create_unit_time(self, course_id, block_id, display_name, total ):
        return CourseUnitTime.objects.create(course_id=course_id, block_id=block_id, display_name=display_name, total=total)
    
    @classmethod
    def get_unit_time (self,  block_id) :
        try:
            return CourseUnitTime.objects.filter( block_id=block_id)[0]
        except :
            return None

    
    @classmethod
    def set_unit_time (self, block_id, total , course_id, display_name):
        try:
   
            total_obj = CourseUnitTime.objects.get(block_id=block_id , course_id = course_id)
            total_obj.total = total
            total_obj.save()
        except CourseUnitTime.DoesNotExist:
            return CourseUnitTime.objects.create(block_id=block_id, total=total, course_id=course_id, display_name=display_name)
        
    @classmethod
    def remove_unit_time_seuqe (self, block_id):
        try:
            return CourseUnitTime.objects.filter(block_id=block_id).delete()
        except:
            return None
    