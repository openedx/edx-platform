"""
Tests for methods defined in mongo_utils.py
"""
import ddt
import os
from unittest import TestCase
from uuid import uuid4

from pymongo import ReadPreference

from django.conf import settings

from xmodule.mongo_utils import connect_to_mongodb


@ddt.ddt
class MongoUtilsTests(TestCase):
    """
    Tests for methods exposed in mongo_utils
    """
    @ddt.data(
        ('PRIMARY', 'primary', ReadPreference.PRIMARY),
        ('SECONDARY_PREFERRED', 'secondaryPreferred', ReadPreference.SECONDARY_PREFERRED),
        ('NEAREST', 'nearest', ReadPreference.NEAREST),
    )
    @ddt.unpack
    def test_connect_to_mongo_read_preference(self, enum_name, mongos_name, expected_read_preference):
        """
        Test that read_preference parameter gets converted to a valid pymongo read preference.
        """
        host = 'edx.devstack.mongo' if 'BOK_CHOY_HOSTNAME' in os.environ else 'localhost'
        db = 'test_read_preference_%s' % uuid4().hex
        # Support for read_preference given in constant name form (ie. PRIMARY, SECONDARY_PREFERRED)
        connection = connect_to_mongodb(db, host, read_preference=enum_name)
        self.assertEqual(connection.client.read_preference, expected_read_preference)
        # Support for read_preference given as mongos name.
        connection = connect_to_mongodb(db, host, read_preference=mongos_name)
        self.assertEqual(connection.client.read_preference, expected_read_preference)
