"""Unit tests for third_party_auth/pipeline.py."""

import random
import mock

from third_party_auth import pipeline
from third_party_auth.tests import testutil
import unittest

from student.views import AccountEmailAlreadyExistsValidationError

# Allow tests access to protected methods (or module-protected methods) under test.
# pylint: disable=protected-access


class MakeRandomPasswordTest(testutil.TestCase):
    """Tests formation of random placeholder passwords."""

    def setUp(self):
        super(MakeRandomPasswordTest, self).setUp()
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


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
class ProviderUserStateTestCase(testutil.TestCase):
    """Tests ProviderUserState behavior."""

    def test_get_unlink_form_name(self):
        google_provider = self.configure_google_provider(enabled=True)
        state = pipeline.ProviderUserState(google_provider, object(), None)
        self.assertEqual(google_provider.provider_id + '_unlink_form', state.get_unlink_form_name())


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
class TestCreateUser(testutil.TestCase):
    """
    Tests for custom create_user step
    """
    def _raise_email_in_use_exception(self, *unused_args, **unused_kwargs):
        """ Helper to raise AccountEmailAlreadyExistsValidationError """
        raise AccountEmailAlreadyExistsValidationError(mock.Mock(), mock.Mock())

    def test_create_user_normal_scenario(self):
        """  Tests happy path - user is created and results are returned intact """
        retval = mock.Mock()
        with mock.patch("third_party_auth.pipeline.social_create_user") as patched_social_create_user:
            patched_social_create_user.return_value = retval
            strategy, details, user, idx = mock.Mock(), {'email': 'qwe@asd.com'}, mock.Mock(), 1

            # pylint: disable=redundant-keyword-arg
            result = pipeline.create_user(strategy, idx, details=details, user=user)

            self.assertEqual(result, retval)

    def test_create_user_exception_scenario(self):
        """
        Tests sad path - expected exception is thrown, captured and transformed into AuthException subclass instance
        """
        with mock.patch("third_party_auth.pipeline.social_create_user") as patched_social_create_user:
            patched_social_create_user.side_effect = self._raise_email_in_use_exception

            strategy, details, user = mock.Mock(), {'email': 'qwe@asd.com'}, mock.Mock()

            with self.assertRaises(pipeline.EmailAlreadyInUseException):
                # pylint: disable=redundant-keyword-arg
                pipeline.create_user(strategy, 1, details=details, user=user)
