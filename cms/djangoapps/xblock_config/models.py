"""
Models used by Studio XBlock infrastructure.

Includes:
    StudioConfig: A ConfigurationModel for managing Studio.
"""


import six
from config_models.models import ConfigurationModel
from django.db.models import TextField
from django.utils.encoding import python_2_unicode_compatible
from opaque_keys.edx.django.models import CourseKeyField

from openedx.core.lib.cache_utils import request_cached


class StudioConfig(ConfigurationModel):
    """
    Configuration for XBlockAsides.

    .. no_pii:
    """
    disabled_blocks = TextField(
        default=u"about course_info static_tab",
        help_text=u"Space-separated list of XBlocks on which XBlockAsides should never render in studio",
    )

    @classmethod
    def asides_enabled(cls, block_type):
        """
        Return True if asides are enabled for this type of block in studio
        """
        studio_config = cls.current()
        return studio_config.enabled and block_type not in studio_config.disabled_blocks.split()


# TODO: Move CourseEditLTIFieldsEnabledFlag to LTI XBlock as a part of EDUCATOR-121
# reference: https://openedx.atlassian.net/browse/EDUCATOR-121
@python_2_unicode_compatible
class CourseEditLTIFieldsEnabledFlag(ConfigurationModel):
    """
    Enables the editing of "request username" and "request email" fields
    of LTI consumer for a specific course.

    .. no_pii:
    """
    KEY_FIELDS = ('course_id',)

    course_id = CourseKeyField(max_length=255, db_index=True)

    @classmethod
    @request_cached()
    def lti_access_to_learners_editable(cls, course_id, is_already_sharing_learner_info):
        """
        Looks at the currently active configuration model to determine whether
        the feature that enables editing of "request username" and "request email"
        fields of LTI consumer is available or not.

        Backwards Compatibility:
        Enable this feature for a course run who was sharing learner username/email
        in the past.

        Arguments:
            course_id (CourseKey): course id for which we need to check this configuration
            is_already_sharing_learner_info (bool): indicates whether LTI consumer is
            already sharing edX learner username/email.
        """
        course_specific_config = (CourseEditLTIFieldsEnabledFlag.objects
                                  .filter(course_id=course_id)
                                  .order_by('-change_date')
                                  .first())

        if is_already_sharing_learner_info:
            if not course_specific_config:
                CourseEditLTIFieldsEnabledFlag.objects.create(course_id=course_id, enabled=True)
                return True

        return course_specific_config.enabled if course_specific_config else False

    def __str__(self):
        en = "Not "
        if self.enabled:
            en = ""

        return u"Course '{course_id}': Edit LTI access to Learner information {en}Enabled".format(
            course_id=six.text_type(self.course_id),
            en=en,
        )
