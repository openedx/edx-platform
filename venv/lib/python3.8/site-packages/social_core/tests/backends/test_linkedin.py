import json

from .oauth import OAuth2Test


class BaseLinkedinTest:
    user_data_url = 'https://api.linkedin.com/v2/me' \
                    '?projection=(firstName,id,lastName)'
    expected_username = 'FooBar'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer'
    })

    # Reference:
    # https://docs.microsoft.com/en-us/linkedin/consumer/integrations/self
    # -serve/sign-in-with-linkedin?context=linkedin/consumer/context#api-request
    user_data_body = json.dumps({
        'id': '1010101010',
        'firstName': {
            'localized': {
                'en_US': 'Foo'
            },
            'preferredLocale': {
                'country': 'US',
                'language': 'en'
            }
        },
        'lastName': {
            'localized': {
                'en_US': 'Bar'
            },
            'preferredLocale': {
                'country': 'US',
                'language': 'en'
            }
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()


class LinkedinOAuth2Test(BaseLinkedinTest, OAuth2Test):
    backend_path = 'social_core.backends.linkedin.LinkedinOAuth2'


class LinkedinMobileOAuth2Test(BaseLinkedinTest, OAuth2Test):
    backend_path = 'social_core.backends.linkedin.LinkedinMobileOAuth2'
