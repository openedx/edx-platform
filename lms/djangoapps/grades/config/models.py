"""
Models for configuration of the feature flags
controlling persistent grades.
"""
from config_models.models import ConfigurationModel
from django.conf import settings
from django.db.models import BooleanField
from xmodule_django.models import CourseKeyField


class PersistentGradesEnabledFlag(ConfigurationModel):
    """
    Enables persistent grades across the platform.
    When this feature flag is set to true, individual courses
    must also have persistent grades enabled for the
    feature to take effect.
    """
    # this field overrides course-specific settings to enable the feature for all courses
    enabled_for_all_courses = BooleanField(default=False)

    @classmethod
    def feature_enabled(cls, course_id=None):
        """
        Looks at the currently active configuration model to determine whether
        the persistent grades feature is available.

        If the flag is not enabled, the feature is not available.
        If the flag is enabled and the provided course_id is for an course
            with persistent grades enabled, the feature is available.
        If the flag is enabled and no course ID is given,
            we return True since the global setting is enabled.
        """
        if settings.FEATURES.get('PERSISTENT_GRADES_ENABLED_FOR_ALL_TESTS'):
            return True
        if not PersistentGradesEnabledFlag.is_enabled():
            return False
        elif not PersistentGradesEnabledFlag.current().enabled_for_all_courses and course_id:
            try:
                return CoursePersistentGradesFlag.objects.get(course_id=course_id).enabled
            except CoursePersistentGradesFlag.DoesNotExist:
                return False
        return True

    class Meta(object):
        app_label = "grades"

    def __unicode__(self):
        current_model = PersistentGradesEnabledFlag.current()
        return u"PersistentGradesEnabledFlag: enabled {}".format(
            current_model.is_enabled()
        )


class CoursePersistentGradesFlag(ConfigurationModel):
    """
    Enables persistent grades for a specific
    course. Only has an effect if the general
    flag above is set to True.
    """
    KEY_FIELDS = ('course_id',)

    class Meta(object):
        app_label = "grades"

    # The course that these features are attached to.
    course_id = CourseKeyField(max_length=255, db_index=True, unique=True)

    def __unicode__(self):
        not_en = "Not "
        if self.enabled:
            not_en = ""
        # pylint: disable=no-member
        return u"Course '{}': Persistent Grades {}Enabled".format(self.course_id.to_deprecated_string(), not_en)
