"""
FieldOverride that forces Show Answer values that use Past Due logic to
new Show Answer values that remove the Past Due check (keeping the rest intact)
"""


from django.conf import settings

from common.lib.xmodule.xmodule.capa_base import SHOWANSWER
from lms.djangoapps.courseware.field_overrides import FieldOverrideProvider
from openedx.features.course_experience import RELATIVE_DATES_FLAG


class ShowAnswerFieldOverride(FieldOverrideProvider):
    """
    A concrete implementation of
    :class:`~courseware.field_overrides.FieldOverrideProvider` which forces
    Show Answer values that use Past Due logic to new Show Answer values
    that remove the Past Due check (keeping the rest intact)

    Once Courseware is able to use BlockTransformers, this override should be
    converted to a BlockTransformer to set the showanswer field.
    """
    def get(self, block, name, default):
        """
        Overwrites the 'showanswer' field on blocks in self-paced courses to
        remove any checks about due dates being in the past.
        """
        if name != 'showanswer':
            return default

        has_showanswer = self.fallback_field_data.has(block, 'showanswer')
        # This is to explicitly check the case where the default value of
        # SHOWANSWER.FINISHED is left on a Course. In that case, we continue
        # to follow the same mapping of FINISHED -> AFTER_ALL_ATTEMPTS_OR_CORRECT.
        # This value will then be inherited throughout the rest of the Course.
        if not has_showanswer and block.category == 'course':
            return SHOWANSWER.AFTER_ALL_ATTEMPTS_OR_CORRECT
        elif not has_showanswer:
            return default

        mapping = {
            SHOWANSWER.ATTEMPTED: SHOWANSWER.ATTEMPTED_NO_PAST_DUE,
            SHOWANSWER.CLOSED: SHOWANSWER.AFTER_ALL_ATTEMPTS,
            SHOWANSWER.CORRECT_OR_PAST_DUE: SHOWANSWER.ANSWERED,
            SHOWANSWER.FINISHED: SHOWANSWER.AFTER_ALL_ATTEMPTS_OR_CORRECT,
            SHOWANSWER.PAST_DUE: SHOWANSWER.NEVER,
        }
        current_show_answer_value = self.fallback_field_data.get(block, 'showanswer')

        return mapping.get(current_show_answer_value, default)

    @classmethod
    def enabled_for(cls, course):
        """ Enabled only for Self-Paced courses using Personalized User Schedules. """
        return course.self_paced and RELATIVE_DATES_FLAG.is_enabled(course.id)
