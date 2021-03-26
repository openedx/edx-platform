"""
Tests for hash_utils.py
"""
from unittest import TestCase

import ddt

from openedx.core.lib.hash_utils import create_hash256, short_token


@ddt.ddt
class TestHashUtils(TestCase):
    """
    Test settings that are derived from other settings.
    """
    def test_short_token(self):
        """
        make sure short token returns 32 size token
        """
        token = short_token()
        assert len(token) == 32

    @ddt.data(0, 10, 30, 64)
    def test_create_hash256_of_size(self, size):
        """
        Test create hash256
        """
        token = create_hash256(size)
        assert len(token) == size

    def test_create_hash256_default(self):
        token = create_hash256()
        assert token is not None
