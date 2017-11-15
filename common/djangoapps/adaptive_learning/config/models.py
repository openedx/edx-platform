"""
Provides configuration models for Adaptive Learning
"""

from config_models.models import ConfigurationModel
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class AdaptiveLearningEnabledFlag(ConfigurationModel):
    """
    A flag that enables/disables the Adaptive Learning feature across an entire instance.

    Defaults to False.
    """

    @classmethod
    def feature_enabled(cls, course_id=None):
        """
        Looks at the currently active configuration model to determine
        whether Adaptive Learning is available (either for an instance
        or for a course).

        If the course_id parameter is passed, it returns a boolean indicating
        whether Adaptive Learning is available for the particular course.
        Note that in order for Adaptive Learning to be available in a given course
        both flags (an instance-wide flag and a course-specific one)
        need to exist and be enabled.

        If the course_id parameter is not passed, it returns a boolean
        specyfing whether Adaptive Learning feature is available instance-wide.
        """

        if AdaptiveLearningEnabledFlag.current().enabled:
            if course_id:
                course_flag = (
                    CourseAdaptiveLearningFlag.objects.filter(course_id=course_id).order_by('-change_date').first()
                )
                return course_flag.enabled if course_flag else False
            else:
                return True
        else:
            return False

    class Meta(object):
        app_label = "adaptive_learning"

    def __unicode__(self):
        current_model = AdaptiveLearningEnabledFlag.current()
        return u"AdaptiveLearningEnabledFlag: enabled {}".format(
            current_model.is_enabled()
        )


class CourseAdaptiveLearningFlag(ConfigurationModel):
    """
    A flag that enables Adaptive Learning for a specific course.
    Only has an effect if the general flag above is set to True.
    If the flag does not exist for a course, it defaults to Adaptive Learning
    not being available for this course.
    """
    KEY_FIELDS = ('course_id',)

    class Meta(object):
        app_label = "adaptive_learning"

    # The course that these features are attached to.
    course_id = CourseKeyField(max_length=255, db_index=True)

    def __unicode__(self):
        not_en = "Not "
        if self.enabled:
            not_en = ""
        # pylint: disable=no-member
        return u"Course '{}': Adaptive Learning {}Enabled".format(self.course_id.to_deprecated_string(), not_en)
