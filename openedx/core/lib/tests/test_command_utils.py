"""
Tests of management command utility code
"""


from unittest import TestCase

import ddt
from django.core.management import CommandError

from .. import command_utils


@ddt.ddt
class MutuallyExclusiveRequiredOptionsTestCase(TestCase):
    """
    Test that mutually exclusive required options allow one and only one option
    to be specified with a true value.
    """
    @ddt.data(
        (['opta'], {'opta': 1}, 'opta'),
        (['opta', 'optb'], {'opta': 1}, 'opta'),
        (['opta', 'optb'], {'optb': 1}, 'optb'),
        (['opta', 'optb'], {'opta': 1, 'optc': 1}, 'opta'),
        (['opta', 'optb'], {'opta': 1, 'optb': 0}, 'opta'),
        (['opta', 'optb', 'optc'], {'optc': 1, 'optd': 1}, 'optc'),
        (['opta', 'optb', 'optc'], {'optc': 1}, 'optc'),
        (['opta', 'optb', 'optc'], {'optd': 0, 'optc': 1}, 'optc'),
    )
    @ddt.unpack
    def test_successful_exclusive_options(self, exclusions, opts, expected):
        result = command_utils.get_mutually_exclusive_required_option(opts, *exclusions)
        self.assertEqual(result, expected)

    @ddt.data(
        (['opta'], {'opta': 0}),
        (['opta', 'optb'], {'opta': 1, 'optb': 1}),
        (['opta', 'optb'], {'optc': 1, 'optd': 1}),
        (['opta', 'optb'], {}),
        (['opta', 'optb', 'optc'], {'opta': 1, 'optc': 1}),
        (['opta', 'optb', 'optc'], {'opta': 1, 'optb': 1}),
        (['opta', 'optb', 'optc'], {'optb': 1, 'optc': 1}),
        (['opta', 'optb', 'optc'], {'opta': 1, 'optb': 1, 'optc': 1}),
        (['opta', 'optb', 'optc'], {}),
    )
    @ddt.unpack
    def test_invalid_exclusive_options(self, exclusions, opts):
        with self.assertRaises(CommandError):
            command_utils.get_mutually_exclusive_required_option(opts, *exclusions)
