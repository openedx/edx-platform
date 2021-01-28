"""
Tests for BlockCompletionTransformer.
"""


from completion.models import BlockCompletion  # lint-amnesty, pylint: disable=import-error
from completion.test_utils import CompletionWaffleTestMixin  # lint-amnesty, pylint: disable=import-error
from xblock.completable import CompletableXBlockMixin, XBlockCompletionMode  # lint-amnesty, pylint: disable=import-error
from xblock.core import XBlock  # lint-amnesty, pylint: disable=import-error

from lms.djangoapps.course_api.blocks.transformers.block_completion import BlockCompletionTransformer
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.course_blocks.transformers.tests.helpers import ModuleStoreTestCase, TransformerRegistryTestMixin
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory  # lint-amnesty, pylint: disable=import-error, wrong-import-order


class StubAggregatorXBlock(XBlock):
    """
    XBlock to test behaviour of BlockCompletionTransformer
    when transforming aggregator XBlock.
    """
    completion_mode = XBlockCompletionMode.AGGREGATOR


class StubExcludedXBlock(XBlock):
    """
    XBlock to test behaviour of BlockCompletionTransformer
    when transforming excluded XBlock.
    """
    completion_mode = XBlockCompletionMode.EXCLUDED


class StubCompletableXBlock(XBlock, CompletableXBlockMixin):
    """
    XBlock to test behaviour of BlockCompletionTransformer
    when transforming completable XBlock.
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


class BlockCompletionTransformerTestCase(TransformerRegistryTestMixin, CompletionWaffleTestMixin, ModuleStoreTestCase):
    """
    Tests behaviour of BlockCompletionTransformer
    """
    TRANSFORMER_CLASS_TO_TEST = BlockCompletionTransformer
    COMPLETION_TEST_VALUE = 0.4

    def setUp(self):
        super(BlockCompletionTransformerTestCase, self).setUp()  # lint-amnesty, pylint: disable=super-with-arguments
        self.user = UserFactory.create(password='test')
        # Set ENABLE_COMPLETION_TRACKING waffle switch to True
        self.override_waffle_switch(True)

    @XBlock.register_temp_plugin(StubAggregatorXBlock, identifier='aggregator')
    def test_transform_gives_none_for_aggregator(self):
        course = CourseFactory.create()
        block = ItemFactory.create(category='aggregator', parent=course)
        block_structure = get_course_blocks(
            self.user, course.location, self.transformers
        )

        self._assert_block_has_proper_completion_value(
            block_structure, block.location, None
        )

    @XBlock.register_temp_plugin(StubExcludedXBlock, identifier='excluded')
    def test_transform_gives_none_for_excluded(self):
        course = CourseFactory.create()
        block = ItemFactory.create(category='excluded', parent=course)
        block_structure = get_course_blocks(
            self.user, course.location, self.transformers
        )

        self._assert_block_has_proper_completion_value(
            block_structure, block.location, None
        )

    @XBlock.register_temp_plugin(StubCompletableXBlock, identifier='comp')
    def test_transform_gives_value_for_completable(self):
        course = CourseFactory.create()
        block = ItemFactory.create(category='comp', parent=course)
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=block.location,
            completion=self.COMPLETION_TEST_VALUE,
        )
        block_structure = get_course_blocks(
            self.user, course.location, self.transformers
        )

        self._assert_block_has_proper_completion_value(
            block_structure, block.location, self.COMPLETION_TEST_VALUE
        )

    def test_transform_gives_zero_for_ordinary_block(self):
        course = CourseFactory.create()
        block = ItemFactory.create(category='html', parent=course)
        block_structure = get_course_blocks(
            self.user, course.location, self.transformers
        )

        self._assert_block_has_proper_completion_value(
            block_structure, block.location, 0.0
        )

    def _assert_block_has_proper_completion_value(
            self, block_structure, block_key, expected_value
    ):
        """
        Checks whether block's completion has expected value.
        """
        block_data = block_structure.get_transformer_block_data(
            block_key, self.TRANSFORMER_CLASS_TO_TEST
        )
        completion_value = block_data.fields['completion']

        self.assertEqual(completion_value, expected_value)
