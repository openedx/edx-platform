"""
Tests for transformer_registry.py
"""

import ddt
from unittest import TestCase

from ..transformer_registry import TransformerRegistry
from .helpers import MockTransformer, mock_registered_transformers


class TestTransformer1(MockTransformer):
    """
    1st test instance of the MockTransformer that is registered.
    """
    pass


class TestTransformer2(MockTransformer):
    """
    2nd test instance of the MockTransformer that is registered.
    """
    pass


class UnregisteredTestTransformer3(MockTransformer):
    """
    3rd test instance of the MockTransformer that is not registered.
    """
    pass


@ddt.ddt
class TransformerRegistryTestCase(TestCase):
    """
    Test cases for TransformerRegistry.
    """
    @ddt.data(
        # None case
        ([], []),

        # 1 registered
        ([TestTransformer1()], []),

        # 2 registered
        ([TestTransformer1(), TestTransformer2()], []),

        # 1 unregistered
        ([UnregisteredTestTransformer3()], [UnregisteredTestTransformer3.name()]),

        # 1 registered and 1 unregistered
        ([TestTransformer1(), UnregisteredTestTransformer3()], [UnregisteredTestTransformer3.name()]),
    )
    @ddt.unpack
    def test_find_unregistered(self, transformers, expected_unregistered):

        with mock_registered_transformers([TestTransformer1, TestTransformer2]):
            self.assertSetEqual(
                TransformerRegistry.find_unregistered(transformers),
                set(expected_unregistered),
            )
