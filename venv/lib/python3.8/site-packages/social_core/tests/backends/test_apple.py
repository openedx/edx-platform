import json
from unittest.mock import patch

from .oauth import OAuth2Test

TEST_KEY = """
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIKQya8aIoeoOLeThk7Ad/lLyAo2fTp9IuhIpy2CivH/qoAoGCCqGSM49
AwEHoUQDQgAEyEY7IMlNJtyaF/pdcM/PpQ8OCe19Sf1Yxq4HQsrB2b7QogB95Vjt
6mTZDAhlXIBtuM/JLrdkMfPmwjVKLgxHAQ==
-----END EC PRIVATE KEY-----
"""


token_data = {
    'sub': '11011110101011011011111011101111',
    'first_name': 'Foo',
    'last_name': 'Bar',
    'email': 'foobar@apple.com',
}


class AppleIdTest(OAuth2Test):
    backend_path = 'social_core.backends.apple.AppleIdAuth'
    user_data_url = 'https://appleid.apple.com/auth/authorize/'
    id_token = 'a-id-token'
    access_token_body = json.dumps({'id_token': id_token, 'access_token': 'a-test-token'})
    expected_username = token_data['sub']

    def extra_settings(self):
        return {
            'SOCIAL_AUTH_' + self.name + '_TEAM': 'a-team-id',
            'SOCIAL_AUTH_' + self.name + '_KEY': 'a-key-id',
            'SOCIAL_AUTH_' + self.name + '_CLIENT': 'a-client-id',
            'SOCIAL_AUTH_' + self.name + '_SECRET': TEST_KEY,
            'SOCIAL_AUTH_' + self.name + '_SCOPE': ['name', 'email'],
        }

    def test_login(self):
        with patch('{}.{}'.format(self.backend_path, 'decode_id_token'),
                   return_value=token_data) as decode_mock:
            self.do_login()
        assert decode_mock.called
        assert decode_mock.call_args[0] == (self.id_token,)

    def test_partial_pipeline(self):
        with patch('{}.{}'.format(self.backend_path, 'decode_id_token'),
                   return_value=token_data) as decode_mock:
            self.do_partial_pipeline()
        assert decode_mock.called
        assert decode_mock.call_args[0] == (self.id_token,)
