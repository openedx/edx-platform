"""
    ORCID OAuth2 Application backend, docs at:
    https://python-social-auth.readthedocs.io/en/latest/backends/orcid.html
"""
from .oauth import BaseOAuth2


class ORCIDOAuth2(BaseOAuth2):
    """ORCID OAuth2 authentication backend"""
    name = 'orcid'
    ID_KEY = 'orcid'
    AUTHORIZATION_URL = 'https://orcid.org/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://orcid.org/oauth/token'
    USER_ID_URL = 'https://orcid.org/oauth/userinfo'
    USER_DATA_URL = 'https://pub.orcid.org/v2.0/{}'
    DEFAULT_SCOPE = ['/authenticate']
    ACCESS_TOKEN_METHOD = 'POST'
    EXTRA_DATA = [
        ('orcid', 'id'),
        ('expires_in', 'expires'),
        ('refresh_token', 'refresh_token')
    ]

    def auth_params(self, state=None):
        params = super().auth_params(state)
        return params

    def get_user_details(self, response):
        """Return user details from ORCID account"""

        # response data will be of the following format:
        # {
        #     'orcid-identifier': {
        #         'uri': 'http://orcid.org/0000-0002-2601-8132',
        #         'path': '0000-0002-2601-8132',
        #         'host': 'orcid.org'
        #     },
        #     'person': {
        #         'last-modified-date': None,
        #         'name': {
        #             'created-date': {
        #                 'value': 1578249746904
        #             },
        #             'last-modified-date': {
        #                 'value': 1578249746904
        #             },
        #             'given-names': {
        #                 'value': 'Janani Kantharooban'
        #             },
        #             'family-name': {
        #                 'value': 'Umachanger'
        #             },
        #             'credit-name': None,
        #             'source': None,
        #             'visibility': 'PUBLIC',
        #             'path': '0000-0002-2601-8132'
        #         },
        #     }
        # }
        orcid_identifier = response.get('orcid-identifier')

        fullname = first_name = last_name = email = username = ''

        person = response.get('person')

        # Although we're checking here, the response will always have the orcid-identifier key:
        if orcid_identifier:
            username = orcid_identifier['path']

        if person:
            name = person.get('name')

            fullname = name

            if name:
                first_name = name.get('given-names', {}).get('value', '')
                last_name = name.get('family-name', {}).get('value', '')

            emails = person.get('emails')
            if emails:
                emails_list = emails.get('email')
                if emails_list and len(emails_list) > 0:
                    email = emails_list[0].get('email', '')

                    if len(emails_list) > 1:
                        for email_dict in emails_list:
                            if email_dict.get('primary'):
                                email = email_dict['email']
                                break
                    else:
                        email = emails_list[0].get('email', '')

        return {
            'username': username,
            'email': email,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name
        }

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service"""
        params = self.setting('PROFILE_EXTRA_PARAMS', {})
        params['access_token'] = access_token

        # Reference Docs: ORCID Auth Flow: https://github.com/ORCID/ORCID-Source/blob/master/orcid-web/ORCID_AUTH_WITH_OPENID_CONNECT.md#other-endpoints
        # Sample headers: -H "Accept: application/json" -H "Authorization: Bearer <access_token>"
        # This will respond with a json document like this:
        # {
        #     "sub":"0000-0002-2601-8132",
        #     "name":"Credit Name",
        #     "family_name":"Jones",
        #     "given_name":"Tom"
        # }
        try:
            response = self.get_json(
                self.USER_ID_URL,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {str(access_token)}'
                },
            )

            # Update Jan 28 2021: Now we definitely have an ORCID id of format "0000-0000-0000-0000"
            orcid = response['sub']
        except Exception as ex:
            pass

        # We can now attempt to access the ORCID public API with the Orcid:
        try:
            return self.get_json(
                    self.USER_DATA_URL.format(orcid),
                    headers={
                        'Content-Type': 'application/json'
                    },
                    params=params
                )
        except Exception as ex:
            return None


class ORCIDOAuth2Sandbox(ORCIDOAuth2):
    """ORCID OAuth2 Sandbox authentication backend"""
    name = 'orcid-sandbox'
    AUTHORIZATION_URL = 'https://sandbox.orcid.org/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://sandbox.orcid.org/oauth/token'
    USER_ID_URL = 'https://sandbox.orcid.org/oauth/userinfo'
    USER_DATA_URL = 'https://pub.sandbox.orcid.org/v2.0/{}'


class ORCIDMemberOAuth2(ORCIDOAuth2):
    """ORCID OAuth2 authentication backend that uses ORCID Member API"""
    USER_DATA_URL = 'https://api.orcid.org/v2.0/{}'
    DEFAULT_SCOPE = ['/authenticate', '/read-limited']


class ORCIDMemberOAuth2Sandbox(ORCIDOAuth2Sandbox):
    """ORCID OAuth2 Sandbox authentication backend that uses ORCID Member Sandbox API"""
    USER_DATA_URL = 'https://api.sandbox.orcid.org/v2.0/{}'
    DEFAULT_SCOPE = ['/authenticate', '/read-limited']
