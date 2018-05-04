"""
Configuration models for Video XModule
"""
from config_models.models import ConfigurationModel
from django.db.models import BooleanField

from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


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
