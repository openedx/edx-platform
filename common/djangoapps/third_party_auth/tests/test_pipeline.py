"""
Unit tests for third_party_auth/pipeline.py.
"""

import random

from third_party_auth import pipeline
from third_party_auth.tests import testutil


# Allow tests access to protected methods (or module-protected methods) under
# test. pylint: disable-msg=protected-access


class MakeRandomPasswordTest(testutil.TestCase):
    """Tests formation of random placeholder passwords."""

    def tearDown(self):
        random.seed()  # Make random random again.
        super(MakeRandomPasswordTest, self).tearDown()

    def test_custom_length(self):
        custom_length = 20
        self.assertEqual(custom_length, len(pipeline.make_random_password(length=custom_length)))

    def test_default_length(self):
        self.assertEqual(pipeline._DEFAULT_RANDOM_PASSWORD_LENGTH, len(pipeline.make_random_password()))

    def test_probably_only_uses_charset(self):
        # This is ultimately probablistic since we could randomly select a good character 100000 consecutive times.
        for char in pipeline.make_random_password(length=100000):
            self.assertIn(char, pipeline._PASSWORD_CHARSET)

    def test_pseudorandomly_picks_chars_from_charset(self):
        seed = 1
        random.seed(seed)
        expected = ''.join(
            random.choice(pipeline._PASSWORD_CHARSET) for _ in xrange(pipeline._DEFAULT_RANDOM_PASSWORD_LENGTH))
        self.assertEqual(expected, pipeline.make_random_password(seed=seed))
