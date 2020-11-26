"""
Tests for extended due date utilities.
"""


import unittest

import mock

from ..util import duedate


class TestGetExtendedDueDate(unittest.TestCase):
    """
    Test `get_extended_due_date` function.
    """

    def call_fut(self, node):
        """
        Call function under test.
        """
        fut = duedate.get_extended_due_date
        return fut(node)

    def test_no_due_date(self):
        """
        Test no due date.
        """
        node = object()
        self.assertEqual(self.call_fut(node), None)

    def test_due_date_no_extension(self):
        """
        Test due date without extension.
        """
        node = mock.Mock(due=1, extended_due=None)
        self.assertEqual(self.call_fut(node), 1)

    def test_due_date_with_extension(self):
        """
        Test due date with extension.
        """
        node = mock.Mock(due=1, extended_due=2)
        self.assertEqual(self.call_fut(node), 2)

    def test_due_date_extension_is_earlier(self):
        """
        Test due date with extension, but due date is later than extension.
        """
        node = mock.Mock(due=2, extended_due=1)
        self.assertEqual(self.call_fut(node), 2)

    def test_extension_without_due_date(self):
        """
        Test non-sensical extension without due date.
        """
        node = mock.Mock(due=None, extended_due=1)
        self.assertEqual(self.call_fut(node), None)

    def test_due_date_with_extension_dict(self):
        """
        Test due date with extension when node is a dict.
        """
        node = {'due': 1, 'extended_due': 2}
        self.assertEqual(self.call_fut(node), 2)
