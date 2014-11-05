"""
Tests for mongodb_proxy.
"""

import unittest

from pymongo.errors import AutoReconnect

from xmodule.modulestore.mongodb_proxy import autoretry_read, MongoProxy


class AutoretryReadDecoratorTestCase(unittest.TestCase):
    """Tests for the autoretry_read decorator."""

    def setUp(self):
        def func():
            """Function to wrap with the decorator."""
            func.call_count += 1
            if func.exceptions_to_raise:
                exception = func.exceptions_to_raise[0]
                func.exceptions_to_raise = func.exceptions_to_raise[1:]
                raise exception
            return "Finished."
        func.exceptions_to_raise = []
        func.call_count = 0
        self.func_to_retry = func

    def test_no_exceptions1(self):
        self.assertEqual(autoretry_read(tries=2)(self.func_to_retry)(), "Finished.")
        self.assertEqual(self.func_to_retry.call_count, 1)

    def test_no_exceptions2(self):
        self.assertEqual(autoretry_read(tries=3)(self.func_to_retry)(), "Finished.")
        self.assertEqual(self.func_to_retry.call_count, 1)

    def test_exceptions1(self):
        with self.assertRaises(ValueError):
            self.func_to_retry.exceptions_to_raise = [ValueError]
            autoretry_read(tries=3)(self.func_to_retry)()
        self.assertEqual(self.func_to_retry.call_count, 1)

    def test_exceptions2(self):
        self.func_to_retry.exceptions_to_raise = [AutoReconnect]
        self.assertEqual(autoretry_read(tries=3)(self.func_to_retry)(), "Finished.")
        self.assertEqual(self.func_to_retry.call_count, 2)

    def test_exceptions3(self):
        with self.assertRaises(AutoReconnect):
            self.func_to_retry.exceptions_to_raise = [AutoReconnect, AutoReconnect, AutoReconnect, AutoReconnect]
            autoretry_read(tries=4)(self.func_to_retry)()
        self.assertEqual(self.func_to_retry.call_count, 4)


class MongoConnection(object):
    """Dummy object to test MongoProxy."""

    def __init__(self, exceptions_to_raise=None):
        self.exceptions_to_raise = exceptions_to_raise
        self.call_count = 0

    def find(self):
        """Method which raises exceptions from list self.exceptions_to_raise."""
        self.call_count += 1
        if self.exceptions_to_raise:
            exception = self.exceptions_to_raise[0]
            self.exceptions_to_raise = self.exceptions_to_raise[1:]
            raise exception
        return "Finished."


class MongoProxyTestCase(unittest.TestCase):
    """Tests for MongoProxy."""

    def test_no_exceptions1(self):
        mongo_connection = MongoProxy(MongoConnection(), methods_needing_retry={MongoConnection: ['find', ]})
        self.assertEqual(mongo_connection.find(), "Finished.")
        self.assertEqual(mongo_connection.call_count, 1)

    def test_exceptions1(self):
        mongo_connection = MongoProxy(
            MongoConnection(exceptions_to_raise=[ValueError]), methods_needing_retry={MongoConnection: ['find', ]}
        )
        with self.assertRaises(ValueError):
            mongo_connection.find()
        self.assertEqual(mongo_connection.call_count, 1)

    def test_exceptions2(self):
        mongo_connection = MongoProxy(
            MongoConnection(exceptions_to_raise=[AutoReconnect, AutoReconnect]),
            methods_needing_retry={MongoConnection: ['find', ]}
        )
        self.assertEqual(mongo_connection.find(), "Finished.")
        self.assertEqual(mongo_connection.call_count, 3)
