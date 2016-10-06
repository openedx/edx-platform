"""
Tests for grades.scores module.
"""
# pylint: disable=protected-access
from collections import namedtuple
import ddt
from django.test import TestCase
import itertools

from lms.djangoapps.grades.models import BlockRecord
import lms.djangoapps.grades.scores as scores
from lms.djangoapps.grades.transformer import GradesTransformer
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from openedx.core.lib.block_structure.block_structure import BlockData
from xmodule.graders import ProblemScore


class TestScoredBlockTypes(TestCase):
    """
    Tests for the possibly_scored function.
    """
    possibly_scored_block_types = {
        'course', 'chapter', 'sequential', 'vertical',
        'library_content', 'split_test', 'conditional', 'library', 'randomize',
        'problem', 'drag-and-drop-v2', 'openassessment', 'lti', 'lti_consumer',
        'videosequence', 'problemset', 'acid_parent', 'done', 'wrapper', 'edx_sga',
    }

    def test_block_types_possibly_scored(self):
        self.assertSetEqual(
            self.possibly_scored_block_types,
            scores._block_types_possibly_scored()
        )

    def test_possibly_scored(self):
        course_key = CourseLocator(u'org', u'course', u'run')
        for block_type in self.possibly_scored_block_types:
            usage_key = BlockUsageLocator(course_key, block_type, 'mock_block_id')
            self.assertTrue(scores.possibly_scored(usage_key))


@ddt.ddt
class TestGetScore(TestCase):
    """
    Tests for get_score
    """
    display_name = 'test_name'
    location = 'test_location'

    SubmissionValue = namedtuple('SubmissionValue', 'exists, weighted_earned, weighted_possible')
    CSMValue = namedtuple('CSMValue', 'exists, raw_earned, raw_possible')
    PersistedBlockValue = namedtuple('PersistedBlockValue', 'exists, raw_possible, weight, graded')
    ContentBlockValue = namedtuple('ContentBlockValue', 'raw_possible, weight, explicit_graded')
    ExpectedResult = namedtuple(
        'ExpectedResult', 'raw_earned, raw_possible, weighted_earned, weighted_possible, weight, graded'
    )

    def _create_submissions_scores(self, submission_value):
        """
        Creates a stub result from the submissions API for the given values.
        """
        if submission_value.exists:
            return {self.location: (submission_value.weighted_earned, submission_value.weighted_possible)}
        else:
            return {}

    def _create_csm_scores(self, csm_value):
        """
        Creates a stub result from courseware student module for the given values.
        """
        if csm_value.exists:
            stub_csm_record = namedtuple('stub_csm_record', 'correct, total')
            return {self.location: stub_csm_record(correct=csm_value.raw_earned, total=csm_value.raw_possible)}
        else:
            return {}

    def _create_persisted_block(self, persisted_block_value):
        """
        Creates and returns a minimal BlockRecord object with the give values.
        """
        if persisted_block_value.exists:
            return BlockRecord(
                self.location,
                persisted_block_value.weight,
                persisted_block_value.raw_possible,
                persisted_block_value.graded,
            )
        else:
            return None

    def _create_block(self, content_block_value):
        """
        Creates and returns a minimal BlockData object with the give values.
        """
        block = BlockData(self.location)
        block.display_name = self.display_name
        block.weight = content_block_value.weight

        block_grades_transformer_data = block.transformer_data.get_or_create(GradesTransformer)
        block_grades_transformer_data.max_score = content_block_value.raw_possible
        setattr(
            block_grades_transformer_data,
            GradesTransformer.EXPLICIT_GRADED_FIELD_NAME,
            content_block_value.explicit_graded,
        )
        return block

    @ddt.data(
        # submissions _trumps_ other values; weighted and graded from persisted-block _trumps_ latest content values
        (
            SubmissionValue(exists=True, weighted_earned=50, weighted_possible=100),
            CSMValue(exists=True, raw_earned=10, raw_possible=40),
            PersistedBlockValue(exists=True, raw_possible=5, weight=40, graded=True),
            ContentBlockValue(raw_possible=1, weight=20, explicit_graded=False),
            ExpectedResult(
                raw_earned=None, raw_possible=None, weighted_earned=50, weighted_possible=100, weight=40, graded=True
            ),
        ),
        # same as above, except submissions doesn't exist; CSM values used
        (
            SubmissionValue(exists=False, weighted_earned=50, weighted_possible=100),
            CSMValue(exists=True, raw_earned=10, raw_possible=40),
            PersistedBlockValue(exists=True, raw_possible=5, weight=40, graded=True),
            ContentBlockValue(raw_possible=1, weight=20, explicit_graded=False),
            ExpectedResult(
                raw_earned=10, raw_possible=40, weighted_earned=10, weighted_possible=40, weight=40, graded=True
            ),
        ),
        # neither submissions nor CSM exist; Persisted values used
        (
            SubmissionValue(exists=False, weighted_earned=50, weighted_possible=100),
            CSMValue(exists=False, raw_earned=10, raw_possible=40),
            PersistedBlockValue(exists=True, raw_possible=5, weight=40, graded=True),
            ContentBlockValue(raw_possible=1, weight=20, explicit_graded=False),
            ExpectedResult(
                raw_earned=0, raw_possible=5, weighted_earned=0, weighted_possible=40, weight=40, graded=True
            ),
        ),
        # none of submissions, CSM, or persisted exist; Latest content values used
        (
            SubmissionValue(exists=False, weighted_earned=50, weighted_possible=100),
            CSMValue(exists=False, raw_earned=10, raw_possible=40),
            PersistedBlockValue(exists=False, raw_possible=5, weight=40, graded=True),
            ContentBlockValue(raw_possible=1, weight=20, explicit_graded=False),
            ExpectedResult(
                raw_earned=0, raw_possible=1, weighted_earned=0, weighted_possible=20, weight=20, graded=False
            ),
        ),
    )
    @ddt.unpack
    def test_get_score(self, submission_value, csm_value, persisted_block_value, block_value, expected_result):
        score = scores.get_score(
            self._create_submissions_scores(submission_value),
            self._create_csm_scores(csm_value),
            self._create_persisted_block(persisted_block_value),
            self._create_block(block_value),
        )
        expected_score = ProblemScore(
            display_name=self.display_name, module_id=self.location, **expected_result._asdict()
        )
        self.assertEquals(score, expected_score)


@ddt.ddt
class TestWeightedScore(TestCase):
    """
    Tests the helper method: weighted_score
    """
    @ddt.data(
        (0, 0, 1),
        (5, 0, 0),
        (10, 0, None),
        (0, 5, None),
        (5, 10, None),
        (10, 10, None),
    )
    @ddt.unpack
    def test_cannot_compute(self, raw_earned, raw_possible, weight):
        self.assertEquals(
            scores.weighted_score(raw_earned, raw_possible, weight),
            (raw_earned, raw_possible),
        )

    @ddt.data(
        (0, 5, 0, (0, 0)),
        (5, 5, 0, (0, 0)),
        (2, 5, 1, (.4, 1)),
        (5, 5, 1, (1, 1)),
        (5, 5, 3, (3, 3)),
        (2, 4, 6, (3, 6)),
    )
    @ddt.unpack
    def test_computed(self, raw_earned, raw_possible, weight, expected_score):
        self.assertEquals(
            scores.weighted_score(raw_earned, raw_possible, weight),
            expected_score,
        )

    def test_assert_on_invalid_r_possible(self):
        with self.assertRaises(AssertionError):
            scores.weighted_score(raw_earned=1, raw_possible=None, weight=1)


@ddt.ddt
class TestInternalGetGraded(TestCase):
    """
    Tests the internal helper method: _get_explicit_graded
    """
    def _create_block(self, explicit_graded_value):
        """
        Creates and returns a minimal BlockData object with the give value
        for explicit_graded.
        """
        block = BlockData('any_key')
        setattr(
            block.transformer_data.get_or_create(GradesTransformer),
            GradesTransformer.EXPLICIT_GRADED_FIELD_NAME,
            explicit_graded_value,
        )
        return block

    @ddt.data(None, True, False)
    def test_with_no_persisted_block(self, explicitly_graded_value):
        block = self._create_block(explicitly_graded_value)
        self.assertEquals(
            scores._get_graded_from_block(None, block),
            explicitly_graded_value is not False,  # defaults to True unless explicitly False
        )

    @ddt.data(
        *itertools.product((True, False), (True, False, None))
    )
    @ddt.unpack
    def test_with_persisted_block(self, persisted_block_value, block_value):
        block = self._create_block(block_value)
        block_record = BlockRecord(block.location, 0, 0, persisted_block_value)
        self.assertEquals(
            scores._get_graded_from_block(block_record, block),
            block_record.graded,  # persisted value takes precedence
        )


@ddt.ddt
class TestInternalGetScoreFromBlock(TestCase):
    """
    Tests the internal helper method: _get_score_from_persisted_or_latest_block
    """
    def _create_block(self, raw_possible):
        """
        Creates and returns a minimal BlockData object with the give value
        for raw_possible.
        """
        block = BlockData('any_key')
        block.transformer_data.get_or_create(GradesTransformer).max_score = raw_possible
        return block

    def _verify_score_result(self, persisted_block, block, weight, expected_r_possible):
        """
        Verifies the result of _get_score_from_persisted_or_latest_block is as expected.
        """
        # pylint: disable=unbalanced-tuple-unpacking
        raw_earned, raw_possible, weighted_earned, weighted_possible = scores._get_score_from_persisted_or_latest_block(
            persisted_block, block, weight,
        )
        self.assertEquals(raw_earned, 0.0)
        self.assertEquals(raw_possible, expected_r_possible)
        self.assertEquals(weighted_earned, 0.0)
        if weight is None or expected_r_possible == 0:
            self.assertEquals(weighted_possible, expected_r_possible)
        else:
            self.assertEquals(weighted_possible, weight)

    @ddt.data(
        *itertools.product((0, 1, 5), (None, 0, 1, 5))
    )
    @ddt.unpack
    def test_with_no_persisted_block(self, block_r_possible, weight):
        block = self._create_block(block_r_possible)
        self._verify_score_result(None, block, weight, block_r_possible)

    @ddt.data(
        *itertools.product((0, 1, 5), (None, 0, 1, 5), (None, 0, 1, 5))
    )
    @ddt.unpack
    def test_with_persisted_block(self, persisted_block_r_possible, block_r_possible, weight):
        block = self._create_block(block_r_possible)
        block_record = BlockRecord(block.location, 0, persisted_block_r_possible, False)
        self._verify_score_result(block_record, block, weight, persisted_block_r_possible)
