"""
Tests for memcache in util app
"""

from django.test import TestCase
from django.core.cache import get_cache
from util.memcache import safe_key


class MemcacheTest(TestCase):
    """
    Test memcache key cleanup
    """

    # Test whitespace, control characters, and some non-ASCII UTF-16
    UNICODE_CHAR_CODES = (range(30) + [127] +
                          [129, 500, 2 ** 8 - 1, 2 ** 8 + 1, 2 ** 16 - 1])

    def setUp(self):
        super(MemcacheTest, self).setUp()
        self.cache = get_cache('default')

    def test_safe_key(self):
        key = safe_key('test', 'prefix', 'version')
        self.assertEqual(key, 'prefix:version:test')

    def test_numeric_inputs(self):

        # Numeric key
        self.assertEqual(safe_key(1, 'prefix', 'version'), 'prefix:version:1')

        # Numeric prefix
        self.assertEqual(safe_key('test', 5, 'version'), '5:version:test')

        # Numeric version
        self.assertEqual(safe_key('test', 'prefix', 5), 'prefix:5:test')

    def test_safe_key_long(self):

        # Choose lengths close to memcached's cutoff (250)
        for length in [248, 249, 250, 251, 252]:

            # Generate a key of that length
            key = 'a' * length

            # Make the key safe
            key = safe_key(key, '', '')

            # The key should now be valid
            self.assertTrue(self._is_valid_key(key),
                            msg="Failed for key length {0}".format(length))

    def test_long_key_prefix_version(self):

        # Long key
        key = safe_key('a' * 300, 'prefix', 'version')
        self.assertTrue(self._is_valid_key(key))

        # Long prefix
        key = safe_key('key', 'a' * 300, 'version')
        self.assertTrue(self._is_valid_key(key))

        # Long version
        key = safe_key('key', 'prefix', 'a' * 300)
        self.assertTrue(self._is_valid_key(key))

    def test_safe_key_unicode(self):

        for unicode_char in self.UNICODE_CHAR_CODES:

            # Generate a key with that character
            key = unichr(unicode_char)

            # Make the key safe
            key = safe_key(key, '', '')

            # The key should now be valid
            self.assertTrue(self._is_valid_key(key),
                            msg="Failed for unicode character {0}".format(unicode_char))

    def test_safe_key_prefix_unicode(self):

        for unicode_char in self.UNICODE_CHAR_CODES:

            # Generate a prefix with that character
            prefix = unichr(unicode_char)

            # Make the key safe
            key = safe_key('test', prefix, '')

            # The key should now be valid
            self.assertTrue(self._is_valid_key(key),
                            msg="Failed for unicode character {0}".format(unicode_char))

    def test_safe_key_version_unicode(self):

        for unicode_char in self.UNICODE_CHAR_CODES:

            # Generate a version with that character
            version = unichr(unicode_char)

            # Make the key safe
            key = safe_key('test', '', version)

            # The key should now be valid
            self.assertTrue(self._is_valid_key(key),
                            msg="Failed for unicode character {0}".format(unicode_char))

    def _is_valid_key(self, key):
        """
        Test that a key is memcache-compatible.
        Based on Django's validator in core.cache.backends.base
        """

        # Check the length
        if len(key) > 250:
            return False

        # Check that there are no spaces or control characters
        for char in key:
            if ord(char) < 33 or ord(char) == 127:
                return False

        return True
