# -*- coding: utf-8 -*-
"""Test for Conditional Xmodule functional logic."""

from xmodule.conditional_module import ConditionalDescriptor
from . import LogicTest


class ConditionalModuleTest(LogicTest):
    """Logic tests for Conditional Xmodule."""
    descriptor_class = ConditionalDescriptor

    def test_ajax_request(self):
        "Make sure that ajax request works correctly"
        # Mock is_condition_satisfied
        self.xmodule.is_condition_satisfied = lambda: True
        self.xmodule.descriptor.get_children = lambda: []

        response = self.ajax_request('No', {})

        self.assertEqual(response, [])
