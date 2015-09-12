"""
Tests for StartDateTransformer.
"""

import ddt
from datetime import timedelta
from django.utils.timezone import now
from mock import patch

from ..start_date import StartDateTransformer, DEFAULT_START_DATE
from .test_helpers import BlockParentsMapTestCase, update_block


@ddt.ddt
class StartDateTransformerTestCase(BlockParentsMapTestCase):
    """
    ...
    """
    class StartDateType(object):
        """
        Use constant enum types for deterministic ddt test method names (rather than dynamically generated timestamps)
        """
        released = 1,
        future = 2,
        default = 3

        TODAY = now()
        LAST_MONTH = TODAY - timedelta(days=30)
        NEXT_MONTH = TODAY + timedelta(days=30)

        @classmethod
        def start(cls, enum_value):
            if enum_value == cls.released:
                return cls.LAST_MONTH
            elif enum_value == cls.future:
                return cls.NEXT_MONTH
            else:
                return DEFAULT_START_DATE

    # Following test cases are based on BlockParentsMapTestCase.parents_map
    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    @ddt.data(
        ({}, {}, {}),
        ({0: StartDateType.default}, {}, {}),
        ({0: StartDateType.future}, {}, {}),
        ({0: StartDateType.released}, {0, 1, 2, 3, 4, 5, 6}, {}),

        # has_access checks on block directly and doesn't follow negative access set on parent/ancestor (i.e., 0)
        ({1: StartDateType.released}, {}, {1, 3, 4, 6}),
        ({2: StartDateType.released}, {}, {2, 5, 6}),
        ({1: StartDateType.released, 2: StartDateType.released}, {}, {1, 2, 3, 4, 5, 6}),

        # DAG conflicts: has_access relies on field inheritance so it takes only the value from the first parent-chain
        ({0: StartDateType.released, 4: StartDateType.future}, {0, 1, 2, 3, 5, 6}, {6}),
        ({0: StartDateType.released, 2: StartDateType.released, 4: StartDateType.future}, {0, 1, 2, 3, 5, 6}, {6}),
        ({0: StartDateType.released, 2: StartDateType.future, 4: StartDateType.released}, {0, 1, 3, 4, 6}, {}),
    )
    @ddt.unpack
    def test_block_start_date(
        self, start_date_type_values, expected_student_visible_blocks, blocks_with_differing_student_access
    ):
        for i, start_date_type in start_date_type_values.iteritems():
            block = self.get_block(i)
            block.start = self.StartDateType.start(start_date_type)
            update_block(block)

        self.check_transformer_results(
            expected_student_visible_blocks, blocks_with_differing_student_access, [StartDateTransformer()]
        )
