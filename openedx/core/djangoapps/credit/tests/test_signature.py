"""
Tests for digital signatures used to validate messages to/from credit providers.
"""


from django.test import TestCase
from django.test.utils import override_settings

from openedx.core.djangoapps.credit import signature


@override_settings(CREDIT_PROVIDER_SECRET_KEYS={
    "asu": 'abcd1234'
})
class SignatureTest(TestCase):
    """
    Tests for digital signatures.
    """

    def test_unicode_secret_key(self):
        # Test a key that has type `unicode` but consists of ASCII characters
        # (This can happen, for example, when loading the key from a JSON configuration file)
        # When retrieving the shared secret, the type should be converted to `str`
        key = signature.get_shared_secret_key("asu")
        sig = signature.signature({}, key)
        assert sig == '7d70a26b834d9881cc14466eceac8d39188fc5ef5ffad9ab281a8327c2c0d093'

    @override_settings(CREDIT_PROVIDER_SECRET_KEYS={
        "asu": '\u4567'
    })
    def test_non_ascii_unicode_secret_key(self):
        # Test a key that contains non-ASCII unicode characters
        # This should return `None` and log an error; the caller
        # is then responsible for logging the appropriate errors
        # so we can fix the misconfiguration.
        key = signature.get_shared_secret_key("asu")
        assert key is None

    def test_unicode_data(self):
        """ Verify the signature generation method supports Unicode data. """
        key = signature.get_shared_secret_key("asu")
        sig = signature.signature({'name': 'Ed Xavíer'}, key)
        assert sig == '76b6c9a657000829253d7c23977b35b34ad750c5681b524d7fdfb25cd5273cec'

    @override_settings(CREDIT_PROVIDER_SECRET_KEYS={
        "asu": 'abcd1234',
    })
    def test_get_shared_secret_key_string(self):
        """
        get_shared_secret_key should return ascii encoded string if provider
        secret is stored as a single key.
        """
        key = signature.get_shared_secret_key("asu")
        assert key == 'abcd1234'

    @override_settings(CREDIT_PROVIDER_SECRET_KEYS={
        "asu": ['abcd1234', 'zyxw9876']
    })
    def test_get_shared_secret_key_string_multiple_keys(self):
        """
        get_shared_secret_key should return ascii encoded strings if provider
        secret is stored as a list for multiple key support.
        """
        key = signature.get_shared_secret_key("asu")
        assert key == ['abcd1234', 'zyxw9876']

    @override_settings(CREDIT_PROVIDER_SECRET_KEYS={
        "asu": ['\u4567', 'zyxw9876']
    })
    def test_get_shared_secret_key_string_multiple_keys_with_none(self):
        """
        get_shared_secret_key should return ascii encoded string if provider
        secret is stored as a list for multiple key support, replacing None
        for unencodable strings.
        """
        key = signature.get_shared_secret_key("asu")
        assert key == [None, 'zyxw9876']
