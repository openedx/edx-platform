"""
Tests for HiddenContentTransformer.
"""


from datetime import timedelta

import ddt
from django.utils.timezone import now

from edx_when.api import get_dates_for_course, set_date_for_block
from edx_when.field_data import DateOverrideTransformer

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.course_blocks.transformers.hidden_content import HiddenContentTransformer
from lms.djangoapps.course_blocks.transformers.tests.helpers import BlockParentsMapTestCase, update_block
from openedx.core.djangoapps.content.block_structure.tests.helpers import mock_registered_transformers
from openedx.core.djangoapps.content.block_structure.transformers import BlockStructureTransformers


@ddt.ddt
class HiddenContentTransformerTestCase(BlockParentsMapTestCase):
    """
    HiddenContentTransformer Test
    """
    TRANSFORMER_CLASS_TO_TEST = HiddenContentTransformer
    ALL_BLOCKS = {0, 1, 2, 3, 4, 5, 6}

    class DueDateType:
        """
        Use constant enum types for deterministic ddt test method names (rather than dynamically generated timestamps)
        """
        none = 1
        future = 2
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
        """ Tests content is hidden if due date is in the past """
        for idx, due_date_type in hide_due_values.items():
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

    def test_hidden_content_with_transformer_override(self):
        """
        Tests content is hidden if the date changes after collection and
        during the transform phase (for example, by the DateOverrideTransformer).
        """
        with mock_registered_transformers([DateOverrideTransformer, self.TRANSFORMER_CLASS_TO_TEST]):
            transformers = BlockStructureTransformers(
                [DateOverrideTransformer(self.student), self.TRANSFORMER_CLASS_TO_TEST()]
            )

        block = self.get_block(1)
        block.hide_after_due = True
        update_block(block)
        set_date_for_block(self.course.id, block.location, 'due', self.DueDateType.PAST_DATE)

        # Due date is in the past so some blocks are hidden
        self.assert_transform_results(
            self.student,
            self.ALL_BLOCKS - {1, 3, 4},
            blocks_with_differing_access=None,
            transformers=transformers,
        )

        # Set an override for the due date to be in the future
        set_date_for_block(self.course.id, block.location, 'due', self.DueDateType.FUTURE_DATE, user=self.student)
        # this line is just to bust the cache for the user so it returns the updated date.
        get_dates_for_course(self.course.id, user=self.student, use_cached=False)

        # Now all blocks are returned for the student
        self.assert_transform_results(
            self.student,
            self.ALL_BLOCKS,
            blocks_with_differing_access=None,
            transformers=transformers,
        )

        # But not for a different user
        different_user = UserFactory()
        with mock_registered_transformers([DateOverrideTransformer, self.TRANSFORMER_CLASS_TO_TEST]):
            transformers = BlockStructureTransformers(
                [DateOverrideTransformer(different_user), self.TRANSFORMER_CLASS_TO_TEST()]
            )
        self.assert_transform_results(
            different_user,
            self.ALL_BLOCKS - {1, 3, 4},
            blocks_with_differing_access=None,
            transformers=transformers,
        )
