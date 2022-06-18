import json
from urllib.parse import urlencode

from .oauth import OAuth2Test


class DropboxOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.dropbox.DropboxOAuth2V2'
    user_data_url = 'https://api.dropboxapi.com/2/users/get_current_account'
    user_data_url_post = True
    expected_username = 'dbidAAH4f99T0taONIb-OurWxbNQ6ywGRopQngc'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'account_id': 'dbid:AAH4f99T0taONIb-OurWxbNQ6ywGRopQngc',
        'name': {
            'given_name': 'Franz',
            'surname': 'Ferdinand',
            'familiar_name': 'Franz',
            'display_name': 'Franz Ferdinand (Personal)',
            'abbreviated_name': 'FF'
        },
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
