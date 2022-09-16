"""
As currently designed, this processor ignores the course specific
`Enable Timed Exams` setting when determining whether or not it should
remove keys and/or supplement exam data. This matches the exact behavior
of `MilestonesAndSpecialExamsTransformer`. It is not entirely clear if
the behavior should be modified, so it has been decided to consider any
necessary fixes in a new ticket.

Please see the PR and discussion linked below for further context
https://github.com/openedx/edx-platform/pull/24545#discussion_r501738511
"""

import logging

from edx_proctoring.api import get_attempt_status_summary
from edx_proctoring.exceptions import ProctoredExamNotFoundException
from django.conf import settings
from django.contrib.auth import get_user_model

from ...data import SpecialExamAttemptData, UserCourseOutlineData
from .base import OutlineProcessor

User = get_user_model()
log = logging.getLogger(__name__)


class SpecialExamsOutlineProcessor(OutlineProcessor):
    """
    Responsible for applying all outline processing related to special exams.
    """
    def load_data(self, full_course_outline):
        """
        Check if special exams are enabled
        """
        self.special_exams_enabled = settings.FEATURES.get('ENABLE_SPECIAL_EXAMS', False)  # lint-amnesty, pylint: disable=attribute-defined-outside-init

    def exam_data(self, pruned_course_outline: UserCourseOutlineData) -> SpecialExamAttemptData:
        """
        Return supplementary special exam information for this outline.

        Be careful to pass in a UserCourseOutlineData - i.e. an outline that has
        already been pruned to what a user is allowed to see. That way, we can
        use this to make sure that we're not returning data about
        LearningSequences that the user can't see because it was hidden by a
        different OutlineProcessor.
        """
        sequences = {}
        if self.special_exams_enabled:
            for section in pruned_course_outline.sections:
                for sequence in section.sequences:
                    # Don't bother checking for information
                    # on non-exam sequences
                    if not bool(sequence.exam):
                        continue

                    special_exam_attempt_context = None
                    try:
                        # Calls into edx_proctoring subsystem to get relevant special exam information.
                        # This will return None, if (user, course_id, content_id) is not applicable.
                        special_exam_attempt_context = get_attempt_status_summary(
                            self.user.id,
                            str(self.course_key),
                            str(sequence.usage_key)
                        )
                    except ProctoredExamNotFoundException:
                        log.info(
                            'No exam found for {sequence_key} in {course_key}'.format(
                                sequence_key=sequence.usage_key,
                                course_key=self.course_key
                            )
                        )

                    if special_exam_attempt_context:
                        # Return exactly the same format as the edx_proctoring API response
                        sequences[sequence.usage_key] = special_exam_attempt_context

        return SpecialExamAttemptData(
            sequences=sequences,
        )
