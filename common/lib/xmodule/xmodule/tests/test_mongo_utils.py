"""Tests for methods defined in mongo_utils.py"""
import os
from unittest import TestCase
from uuid import uuid4

from pymongo import ReadPreference

from django.conf import settings

from xmodule.mongo_utils import connect_to_mongodb


class MongoUtilsTests(TestCase):
    """
    Tests for methods exposed in mongo_utils
    """
    def test_connect_to_mongo_read_preference(self):
        """
        Test that read_preference parameter gets converted to a valid pymongo read preference.
        """
        host = 'edx.devstack.mongo' if 'BOK_CHOY_HOSTNAME' in os.environ else 'localhost'
        db = 'test_read_preference_%s' % uuid4().hex
        # Support for read_preference given in constant name form (ie. PRIMARY, SECONDARY_PREFERRED)
        connection = connect_to_mongodb(db, host, read_preference='SECONDARY_PREFERRED')
        self.assertEqual(connection.client.read_preference, ReadPreference.SECONDARY_PREFERRED)
        # Support for read_preference given as mongos name.
        connection = connect_to_mongodb(db, host, read_preference='secondaryPreferred')
        self.assertEqual(connection.client.read_preference, ReadPreference.SECONDARY_PREFERRED)
