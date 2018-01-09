"""
Models for configuration of the feature flags
controlling the new assets page.
"""
from config_models.models import ConfigurationModel
from django.db.models import BooleanField
from six import text_type
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class NewAssetsPageFlag(ConfigurationModel):
    """
    Enables the in-development new assets page from studio-frontend.

    Defaults to False platform-wide, but can be overriden via a course-specific
    flag. The idea is that we can use this to do a gradual rollout, and remove
    the flag entirely once generally released to everyone.
    """
    # this field overrides course-specific settings to enable the feature for all courses
    enabled_for_all_courses = BooleanField(default=False)

    @classmethod
    def feature_enabled(cls, course_id=None):
        """
        Looks at the currently active configuration model to determine whether
        the new assets page feature is available.

        There are 2 booleans to be concerned with - enabled_for_all_courses,
        and the implicit is_enabled(). They interact in the following ways:
            - is_enabled: False, enabled_for_all_courses: True or False
                - no one can use the feature.
            - is_enabled: True, enabled_for_all_courses: False
                - check for a CourseNewAssetsPageFlag, use that value (default False)
                - if no course_id provided, return False
            - is_enabled: True, enabled_for_all_courses: True
                - everyone can use the feature
        """
        if not NewAssetsPageFlag.is_enabled():
            return False
        elif not NewAssetsPageFlag.current().enabled_for_all_courses:
            if course_id:
                effective = CourseNewAssetsPageFlag.objects.filter(course_id=course_id).order_by('-change_date').first()
                return effective.enabled if effective is not None else False
            else:
                return False
        else:
            return True

    class Meta(object):
        app_label = "contentstore"

    def __unicode__(self):
        current_model = NewAssetsPageFlag.current()
        return u"NewAssetsPageFlag: enabled {}".format(
            current_model.is_enabled()
        )


class CourseNewAssetsPageFlag(ConfigurationModel):
    """
    Enables new assets page for a specific
    course. Only has an effect if the general
    flag above is set to True.
    """
    KEY_FIELDS = ('course_id',)

    class Meta(object):
        app_label = "contentstore"

    # The course that these features are attached to.
    course_id = CourseKeyField(max_length=255, db_index=True)

    def __unicode__(self):
        not_en = "Not "
        if self.enabled:
            not_en = ""
        # pylint: disable=no-member
        return u"Course '{}': New assets page {}Enabled".format(text_type(self.course_id), not_en)
