"""
FieldOverride that forces Show Answer values that use Past Due logic to
new Show Answer values that remove the Past Due check (keeping the rest intact)
"""

from lms.djangoapps.courseware.field_overrides import FieldOverrideProvider
from openedx.features.course_experience import RELATIVE_DATES_FLAG
from xmodule.graders import ShowAnswer


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
        if name != 'showanswer' or not self.fallback_field_data.has(block, 'showanswer'):
            return default

        mapping = {
            ShowAnswer.ATTEMPTED: ShowAnswer.ATTEMPTED_NO_PAST_DUE,
            ShowAnswer.CLOSED: ShowAnswer.AFTER_ALL_ATTEMPTS,
            ShowAnswer.CORRECT_OR_PAST_DUE: ShowAnswer.ANSWERED,
            ShowAnswer.FINISHED: ShowAnswer.AFTER_ALL_ATTEMPTS_OR_CORRECT,
            ShowAnswer.PAST_DUE: ShowAnswer.NEVER,
        }
        current_show_answer_value = self.fallback_field_data.get(block, 'showanswer')

        return mapping.get(current_show_answer_value, default)

    @classmethod
    def enabled_for(cls, course):  # pylint: disable=arguments-differ
        """ Enabled only for Self-Paced courses using Personalized User Schedules. """
        return course and course.self_paced and RELATIVE_DATES_FLAG.is_enabled(course.id)
