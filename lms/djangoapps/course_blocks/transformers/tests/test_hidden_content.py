"""
Tests for HiddenContentTransformer.
"""
from datetime import timedelta
import ddt
from django.utils.timezone import now
from nose.plugins.attrib import attr

from ..hidden_content import HiddenContentTransformer
from .helpers import BlockParentsMapTestCase, update_block


@attr('shard_3')
@ddt.ddt
class HiddenContentTransformerTestCase(BlockParentsMapTestCase):
    """
    VisibilityTransformer Test
    """
    TRANSFORMER_CLASS_TO_TEST = HiddenContentTransformer
    ALL_BLOCKS = {0, 1, 2, 3, 4, 5, 6}

    class DueDateType(object):
        """
        Use constant enum types for deterministic ddt test method names (rather than dynamically generated timestamps)
        """
        none = 1,
        future = 2,
        past = 3

        TODAY = now()
        PAST_DATE = TODAY - timedelta(days=30)
        FUTURE_DATE = TODAY + timedelta(days=30)

        @classmethod
        def due(cls, enum_value):
            """
            Returns a start date for the given enum value
            """
            if enum_value == cls.future:
                return cls.FUTURE_DATE
            elif enum_value == cls.past:
                return cls.PAST_DATE
            else:
                return None

    # Following test cases are based on BlockParentsMapTestCase.parents_map
    @ddt.data(
        ({}, ALL_BLOCKS),

        ({0: DueDateType.none}, ALL_BLOCKS),
        ({0: DueDateType.future}, ALL_BLOCKS),
        ({1: DueDateType.none}, ALL_BLOCKS),
        ({1: DueDateType.future}, ALL_BLOCKS),
        ({4: DueDateType.none}, ALL_BLOCKS),
        ({4: DueDateType.future}, ALL_BLOCKS),

        ({0: DueDateType.past}, {}),
        ({1: DueDateType.past}, ALL_BLOCKS - {1, 3, 4}),
        ({2: DueDateType.past}, ALL_BLOCKS - {2, 5}),
        ({4: DueDateType.past}, ALL_BLOCKS - {4}),

        ({1: DueDateType.past, 2: DueDateType.past}, {0}),
        ({1: DueDateType.none, 2: DueDateType.past}, ALL_BLOCKS - {2, 5}),
        ({1: DueDateType.past, 2: DueDateType.none}, ALL_BLOCKS - {1, 3, 4}),
    )
    @ddt.unpack
    def test_hidden_content(
            self,
            hide_due_values,
            expected_visible_blocks,
    ):
        for idx, due_date_type in hide_due_values.iteritems():
            block = self.get_block(idx)
            block.due = self.DueDateType.due(due_date_type)
            block.hide_after_due = True
            update_block(block)

        self.assert_transform_results(
            self.student,
            expected_visible_blocks,
            blocks_with_differing_access=None,
            transformers=self.transformers,
        )
