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

    def setUp(self):
        super(MakeRandomPasswordTest, self).tearDown()
        self.seed = 1

    def test_default_args(self):
        self.assertEqual(pipeline._DEFAULT_RANDOM_PASSWORD_LENGTH, len(pipeline.make_random_password()))

    def test_probably_only_uses_charset(self):
        # This is ultimately probablistic since we could randomly select a good character 100000 consecutive times.
        for char in pipeline.make_random_password(length=100000):
            self.assertIn(char, pipeline._PASSWORD_CHARSET)

    def test_pseudorandomly_picks_chars_from_charset(self):
        random_instance = random.Random(self.seed)
        expected = ''.join(
            random_instance.choice(pipeline._PASSWORD_CHARSET)
            for _ in xrange(pipeline._DEFAULT_RANDOM_PASSWORD_LENGTH))
        random_instance.seed(self.seed)
        self.assertEqual(expected, pipeline.make_random_password(choice_fn=random_instance.choice))
