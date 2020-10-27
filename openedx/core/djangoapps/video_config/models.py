"""
Configuration models for Video XModule
"""
from django.db import models
from django.db.models import BooleanField, TextField, PositiveIntegerField
from config_models.models import ConfigurationModel
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField


URL_REGEX = r'^[a-zA-Z0-9\-_]*$'


class HLSPlaybackEnabledFlag(ConfigurationModel):
    """
    Enables HLS Playback across the platform.
    When this feature flag is set to true, individual courses
    must also have HLS Playback enabled for this feature to
    take effect.
    """
    # this field overrides course-specific settings
    enabled_for_all_courses = BooleanField(default=False)

    @classmethod
    def feature_enabled(cls, course_id):
        """
        Looks at the currently active configuration model to determine whether
        the HLS Playback feature is available.

        If the feature flag is not enabled, the feature is not available.
        If the flag is enabled for all the courses, feature is available.
        If the flag is enabled and the provided course_id is for an course
            with HLS Playback enabled, the feature is available.

        Arguments:
            course_id (CourseKey): course id for whom feature will be checked.
        """
        if not HLSPlaybackEnabledFlag.is_enabled():
            return False
        elif not HLSPlaybackEnabledFlag.current().enabled_for_all_courses:
            feature = (CourseHLSPlaybackEnabledFlag.objects
                       .filter(course_id=course_id)
                       .order_by('-change_date')
                       .first())
            return feature.enabled if feature else False
        return True

    def __unicode__(self):
        current_model = HLSPlaybackEnabledFlag.current()
        return u"HLSPlaybackEnabledFlag: enabled {is_enabled}".format(
            is_enabled=current_model.is_enabled()
        )


class CourseHLSPlaybackEnabledFlag(ConfigurationModel):
    """
    Enables HLS Playback for a specific course. Global feature must be
    enabled for this to take effect.
    """
    KEY_FIELDS = ('course_id',)

    course_id = CourseKeyField(max_length=255, db_index=True)

    def __unicode__(self):
        not_en = "Not "
        if self.enabled:
            not_en = ""

        return u"Course '{course_key}': HLS Playback {not_enabled}Enabled".format(
            course_key=unicode(self.course_id),
            not_enabled=not_en
        )


class VideoTranscriptEnabledFlag(ConfigurationModel):
    """
    Enables Video Transcript across the platform.
    When this feature flag is set to true, individual courses
    must also have Video Transcript enabled for this feature to
    take effect.
    When this feature is enabled, 3rd party transcript integration functionality would be available accross all
    courses or some specific courses and S3 video transcript would be served (currently as a fallback).
    """
    # this field overrides course-specific settings
    enabled_for_all_courses = BooleanField(default=False)

    @classmethod
    def feature_enabled(cls, course_id):
        """
        Looks at the currently active configuration model to determine whether
        the Video Transcript feature is available.

        If the feature flag is not enabled, the feature is not available.
        If the flag is enabled for all the courses, feature is available.
        If the flag is enabled and the provided course_id is for an course
            with Video Transcript enabled, the feature is available.

        Arguments:
            course_id (CourseKey): course id for whom feature will be checked.
        """
        if not VideoTranscriptEnabledFlag.is_enabled():
            return False
        elif not VideoTranscriptEnabledFlag.current().enabled_for_all_courses:
            feature = (CourseVideoTranscriptEnabledFlag.objects
                       .filter(course_id=course_id)
                       .order_by('-change_date')
                       .first())
            return feature.enabled if feature else False
        return True

    def __unicode__(self):
        current_model = VideoTranscriptEnabledFlag.current()
        return u"VideoTranscriptEnabledFlag: enabled {is_enabled}".format(
            is_enabled=current_model.is_enabled()
        )


class CourseVideoTranscriptEnabledFlag(ConfigurationModel):
    """
    Enables Video Transcript for a specific course. Global feature must be
    enabled for this to take effect.
    When this feature is enabled, 3rd party transcript integration functionality would be available for the
    specific course and S3 video transcript would be served (currently as a fallback).
    """
    KEY_FIELDS = ('course_id',)

    course_id = CourseKeyField(max_length=255, db_index=True)

    def __unicode__(self):
        not_en = "Not "
        if self.enabled:
            not_en = ""

        return u"Course '{course_key}': Video Transcript {not_enabled}Enabled".format(
            course_key=unicode(self.course_id),
            not_enabled=not_en
        )


class TranscriptMigrationSetting(ConfigurationModel):
    """
    Arguments for the Transcript Migration management command
    """
    def __unicode__(self):
        return (
            "[TranscriptMigrationSetting] Courses {courses} with update if already present as {force}"
            " and commit as {commit}"
        ).format(
            courses='ALL' if self.all_courses else self.course_ids,
            force=self.force_update,
            commit=self.commit
        )
    force_update = BooleanField(
        default=False,
        help_text="Flag to force migrate transcripts for the requested courses, overwrite if already present."
    )
    command_run = PositiveIntegerField(default=0)
    batch_size = PositiveIntegerField(default=0)
    commit = BooleanField(
        default=False,
        help_text="Dry-run or commit."
    )
    all_courses = BooleanField(
        default=False,
        help_text="Process all courses."
    )
    course_ids = TextField(
        blank=False,
        help_text="Whitespace-separated list of course keys for which to migrate transcripts."
    )

    def increment_run(self):
        """
        Increments the run which indicates how many time the mgmt. command has run.
        """
        self.command_run += 1
        self.save()
        return self.command_run


class MigrationEnqueuedCourse(TimeStampedModel):
    """
    Temporary model to persist the course IDs who has been enqueued for transcripts migration to S3.
    """
    course_id = CourseKeyField(db_index=True, primary_key=True, max_length=255)
    command_run = PositiveIntegerField(default=0)

    def __unicode__(self):
        return u'MigrationEnqueuedCourse: ID={course_id}, Run={command_run}'.format(
            course_id=self.course_id, command_run=self.command_run
        )


class VideoThumbnailSetting(ConfigurationModel):
    """
    Arguments for the Video Thumbnail management command
    """
    command_run = PositiveIntegerField(default=0)
    offset = PositiveIntegerField(default=0)
    batch_size = PositiveIntegerField(default=0)
    videos_per_task = PositiveIntegerField(default=0)
    commit = BooleanField(
        default=False,
        help_text="Dry-run or commit."
    )
    all_course_videos = BooleanField(
        default=False,
        help_text="Process all videos."
    )
    course_ids = TextField(
        blank=True,
        help_text="Whitespace-separated list of course ids for which to update videos."
    )

    def increment_run(self):
        """
        Increments the run which indicates the management command run count.
        """
        self.command_run += 1
        self.save()
        return self.command_run

    def update_offset(self):
        self.offset += self.batch_size
        self.save()

    def __unicode__(self):
        return "[VideoThumbnailSetting] update for {courses} courses if commit as {commit}".format(
            courses='ALL' if self.all_course_videos else self.course_ids,
            commit=self.commit,
        )


class UpdatedCourseVideos(TimeStampedModel):
    """
    Temporary model to persist the course videos which have been enqueued to update video thumbnails.
    """
    course_id = CourseKeyField(db_index=True, max_length=255)
    edx_video_id = models.CharField(max_length=100)
    command_run = PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('course_id', 'edx_video_id')

    def __unicode__(self):
        return u'UpdatedCourseVideos: CourseID={course_id}, VideoID={video_id}, Run={command_run}'.format(
            course_id=self.course_id, video_id=self.edx_video_id, command_run=self.command_run
        )
