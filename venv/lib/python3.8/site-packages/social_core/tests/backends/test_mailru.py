import json

from .oauth import OAuth2Test


class MRGOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.mailru.MRGOAuth2'
    user_data_url = 'https://oauth.mail.ru/userinfo'
    expected_username = 'FooBar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })
    user_data_body = json.dumps({
        'first_name': 'Foo',
        'last_name': 'Bar',
        'name': 'Foo Bar',
        'locale': 'ru_RU',
        'email': 'foobar@example.com',
        'birthday': '11.07.1970',
        'gender': 'm',
        'image': 'http://cs7003.vk.me/v7003815/22a1/xgG9fb-IJ3Y.jpg',

    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
