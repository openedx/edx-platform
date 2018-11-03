"""
Test Scorable block.
"""

# pylint: disable=protected-access

from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

import ddt
from mock import Mock

from xblock import scorable


class StubScorableBlock(scorable.ScorableXBlockMixin):
    """
    A very simple scorable block that needs no backing
    """
    location = 'Here'

    _scoring_error = False
    _allows_rescore = None

    def __init__(self, initial):
        self.result = initial
        self.runtime = Mock()

    def allows_rescore(self):
        if self._allows_rescore is not None:
            return self._allows_rescore
        else:
            return super(StubScorableBlock, self).allows_rescore()

    def has_submitted_answer(self):
        return self.get_score() is not None

    def get_score(self):
        return self.result

    def set_score(self, score):
        self.result = score

    def calculate_score(self):
        if self._scoring_error:
            raise RuntimeError('Whoops')  # Any error will do
        else:
            return scorable.Score(raw_earned=1.6, raw_possible=2.0)


@ddt.ddt
class RescoreTestCase(TestCase):
    """
    Test scorable block behavior
    """
    @ddt.data(True, False)
    def test_basic(self, only_if_higher):
        block = StubScorableBlock(scorable.Score(raw_earned=2.0, raw_possible=2.0))
        block.rescore(only_if_higher=only_if_higher)

        # The new score is published to the grade infrastructure with
        # only_if_higher set appropriately.
        block.runtime.publish.assert_called_with(
            block,
            'grade',
            {
                'value': 1.6,
                'max_value': 2.0,
                'only_if_higher': only_if_higher,
            }
        )

    def test_not_yet_scored(self):
        block = StubScorableBlock(None)
        with self.assertRaises(ValueError):
            block.rescore(only_if_higher=False)

    def test_disallow_rescore(self):
        block = StubScorableBlock(scorable.Score(raw_earned=0.0, raw_possible=1.0))
        block._allows_rescore = False
        with self.assertRaises(TypeError):
            block.rescore(only_if_higher=False)

    def test_scoring_error(self):
        block = StubScorableBlock(scorable.Score(raw_earned=0.0, raw_possible=1.0))
        block._scoring_error = True
        with self.assertRaises(RuntimeError):
            block.rescore(only_if_higher=False)
