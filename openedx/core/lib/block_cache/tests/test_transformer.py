"""
Tests for transformer.py
"""

from mock import patch
from unittest import TestCase

from ..transformer import BlockStructureTransformers
from .test_utils import MockTransformer


class BlockStructureTransformersTestCase(TestCase):
    """
    Test cases for BlockStructureTransformers.
    """
    class TestTransformer1(MockTransformer):
        pass

    class TestTransformer2(MockTransformer):
        pass

    class UnregisteredTestTransformer3(MockTransformer):
        pass

    @patch('openedx.core.lib.block_cache.transformer.BlockStructureTransformers.get_available_plugins')
    def test_find_unregistered(self, mock_available_transforms):

        mock_available_transforms.return_value = {
            transformer.name(): transformer
            for transformer in [self.TestTransformer1, self.TestTransformer2]
        }

        for transformers, expected_find_unregistered in [
            ([], []),
            ([self.TestTransformer1()], []),
            ([self.TestTransformer1(), self.TestTransformer2()], []),
            (
                [self.UnregisteredTestTransformer3()],
                [self.UnregisteredTestTransformer3.name()]
            ),
            (
                [self.TestTransformer1(), self.UnregisteredTestTransformer3()],
                [self.UnregisteredTestTransformer3.name()]
            ),
        ]:
            self.assertSetEqual(
                BlockStructureTransformers.find_unregistered(transformers), set(expected_find_unregistered)
            )
