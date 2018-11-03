"""
Scorable.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from collections import namedtuple
import logging


log = logging.getLogger(__name__)


Score = namedtuple('Score', ['raw_earned', 'raw_possible'])


class ScorableXBlockMixin(object):
    """
    Mixin to handle functionality related to scoring.

    Subclasses must define the following:

        ScorableXBlockMixin.has_submitted_answer(self)
        ScorableXBlockMixin.get_score(self)
        ScorableXBlockMixin.set_score(self, score)
        ScorableXBlockMixin.calculate_score(self, score)

    Legacy scorable blocks are identified in edx-platform by the presence of a
    "has_score" boolean attribute.  We maintain that identifier here.
    """

    has_score = True

    def rescore(self, only_if_higher):
        """
        Calculate a new raw score and save it to the block.  If only_if_higher
        is True and the score didn't improve, keep the existing score.

        Raises a TypeError if the block cannot be scored.
        Raises a ValueError if the user has not yet completed the problem.

        May also raise other errors in self.calculate_score().  Currently
        unconstrained.
        """

        _ = self.runtime.service(self, 'i18n').ugettext

        if not self.allows_rescore():
            raise TypeError(_('Problem does not support rescoring: {}').format(self.location))

        if not self.has_submitted_answer():
            raise ValueError(_('Cannot rescore unanswered problem: {}').format(self.location))

        new_score = self.calculate_score()
        self._publish_grade(new_score, only_if_higher)

    def allows_rescore(self):
        """
        Boolean value: Can this problem be rescored?

        Subtypes may wish to override this if they need conditional support for
        rescoring.
        """
        return True

    def has_submitted_answer(self):
        """
        Returns True if the problem has been answered by the runtime user.
        """
        raise NotImplementedError

    def get_score(self):
        """
        Return a raw score already persisted on the XBlock.  Should not
        perform new calculations.

        Returns:
            Score(raw_earned=float, raw_possible=float)
        """
        raise NotImplementedError

    def set_score(self, score):
        """
        Persist a score to the XBlock.

        The score is a named tuple with a raw_earned attribute and a
        raw_possible attribute, reflecting the raw earned score and the maximum
        raw score the student could have earned respectively.

        Arguments:
            score: Score(raw_earned=float, raw_possible=float)

        Returns:
            None
        """
        raise NotImplementedError

    def calculate_score(self):
        """
        Calculate a new raw score based on the state of the problem.
        This method should not modify the state of the XBlock.

        Returns:
            Score(raw_earned=float, raw_possible=float)
        """
        raise NotImplementedError

    def _publish_grade(self, score, only_if_higher=None):
        """
        Publish a grade to the runtime.
        """
        grade_dict = {
            'value': score.raw_earned,
            'max_value': score.raw_possible,
            'only_if_higher': only_if_higher,
        }
        self.runtime.publish(self, 'grade', grade_dict)
