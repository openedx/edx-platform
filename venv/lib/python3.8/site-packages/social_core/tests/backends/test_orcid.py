import json

from social_core.backends.orcid import ORCIDOAuth2

from .oauth import OAuth2Test


class ORCIDOAuth2Test(OAuth2Test):
    backend_path = 'social_core.backends.orcid.ORCIDOAuth2'
    user_data_url = ORCIDOAuth2.USER_ID_URL
    expected_username = '0000-0002-2601-8132'
    access_token_body = json.dumps({
        'access_token': 'foobar',
        'token_type': 'bearer',
        'orcid-identifier': {
            'path': '0000-0002-2601-8132'
        },
    })
    user_data_body = json.dumps({
        'orcid-identifier': {
            'uri': 'http://orcid.org/0000-0002-2601-8132',
            'path': '0000-0002-2601-8132',
            'host': 'orcid.org'
        },
        'person': {
            'last-modified-date': None,
            'name': {
                'created-date': {
                    'value': 1578249746904
                },
                'last-modified-date': {
                    'value': 1578249746904
                },
                'given-names': {
                    'value': 'Janani Kantharooban'
                },
                'family-name': {
                    'value': 'Umachanger'
                },
                'credit-name': None,
                'source': None,
                'visibility': 'PUBLIC',
                'path': '0000-0002-2601-8132'
            },
            'other-names': {
                'last-modified-date': None,
                'other-name': [],
                'path': '/0000-0002-2601-8132/other-names'
            },
            'biography': None,
            'researcher-urls': {
                'last-modified-date': None,
                'researcher-url': [],
                'path': '/0000-0002-2601-8132/researcher-urls'
            },
            'emails': {
                'last-modified-date': None,
                'email': [],
                'path': '/0000-0002-2601-8132/email'
            },
            'addresses': {
                'last-modified-date': None,
                'address': [],
                'path': '/0000-0002-2601-8132/address'
            },
            'keywords': {
                'last-modified-date': None,
                'keyword': [],
                'path': '/0000-0002-2601-8132/keywords'
            },
            'external-identifiers': {
                'last-modified-date': None,
                'external-identifier': [],
                'path': '/0000-0002-2601-8132/external-identifiers'
            },
            'path': '/0000-0002-2601-8132/person'
        }
    })

    def test_login(self):
        self.do_login()

    def test_partial_pipeline(self):
        self.do_partial_pipeline()
