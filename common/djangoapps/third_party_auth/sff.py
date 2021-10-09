"""
SFFOAuth2: SFF OAuth2
"""

import urllib
from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthFailed
from social_core.utils import handle_http_errors
from common.djangoapps import third_party_auth

class SFFOAuth2(BaseOAuth2):  # pylint: disable=abstract-method
    """
    python-social-auth backend that doesn't actually go to any third party site
    """
    name = "sff-oauth2"
    SUCCEED = True  # You can patch this during tests in order to control whether or not login works

    PROVIDER_URL = "https://dev-973880.okta.com/"
    AUTHORIZE_URL = "/oauth2/v1/authorize"  # '/oauth2/authorize' usually is default value
    GET_TOKEN_URL = "/oauth2/v1/token"  # '/oauth2/token' usually is default value
    ID_KEY = "sub"  # unique marker which could be taken from the SSO response
    USER_DATA_URL = "/oauth2/v1/userinfo"  # '/api/current-user/' some url similar to the example

    AUTHORIZATION_URL = urllib.parse.urljoin(PROVIDER_URL, AUTHORIZE_URL)
    ACCESS_TOKEN_URL = urllib.parse.urljoin(PROVIDER_URL, GET_TOKEN_URL)
    # DEFAULT_SCOPE = settings.FEATURES.get('SCOPE')  # extend the scope of the provided permissions.
    DEFAULT_SCOPE = ['openid','profile','email']
    REDIRECT_STATE = False
    ACCESS_TOKEN_METHOD = 'POST'  # default method is 'GET'

    skip_email_verification = True

    def setting(self, name, default=None):
        """
        Return setting value from strategy.
        """
        if third_party_auth.models.OAuth2ProviderConfig is not None:
            providers = [
                p for p in third_party_auth.provider.Registry.displayed_for_login() if p.backend_name == self.name
            ]
            if not providers:
                raise Exception("Can't fetch setting of a disabled backend.")
            provider_config = providers[0]
            try:
                return provider_config.get_setting(name)
            except KeyError:
                pass
        return super(SFFOAuth2, self).setting(name, default=default)

    def get_user_details(self, response):
        print('GGWP get_user_details')
        """
        Return user details from SSO account.
        """
        return {'username': response.get('sub'),
                'name': response.get('sub'),
                'fullname': response.get('sub'),  
                'email': response.get('email') or '',
                'first_name': response.get('given_name'),
                'last_name': response.get('family_name')}

    @handle_http_errors
    def do_auth(self, access_token, *args, **kwargs):
        print('GGWP do_auth v2')
        """
        Finish the auth process once the access_token was retrieved.
        """
        data = self.user_data(access_token, *args, **kwargs)
        print('GGWP do_auth data',data)
        if data is not None and 'access_token' not in data:
            data['access_token'] = access_token
        kwargs.update({'response': data, 'backend': self})
        return self.strategy.authenticate(*args, **kwargs)

    @handle_http_errors
    def auth_complete(self, *args, **kwargs):
        print('GGWP auth_complete')
        """
        Complete loging process, must return user instance.
        """
        self.strategy.session_set('{}_state'.format(self.name), self.data.get('state'))
        next_url = '/'
        self.strategy.session.setdefault('next', next_url)
        return super(SFFOAuth2, self).auth_complete(*args, **kwargs)

    def user_data(self, access_token, *args, **kwargs):
        print('GGWP user_data')
        print(f' Args: {args}' )
        print(f' Kwargs: {kwargs}' )
        print('GGWP user_data access_token',access_token)
        """
        Grab user profile information from SSO.
        """
        header = {"Authorization": "Bearer %s" % access_token}
        data = self.get_json('https://dev-973880.okta.com/oauth2/v1/userinfo', headers=header)
        print('GGWP user_data A')
        print('GGWP user_data data',data)
        # data = self.get_json(
        #     urllib.parse.urljoin(self.PROVIDER_URL, self.USER_DATA_URL),
        #     params={'access_token': access_token},
        # )
        data['access_token'] = access_token
        return data

    def get_user_id(self, details, response):
        print('GGWP get_user_id')
        """
        Return a unique ID for the current user, by default from server response.
        """
        if 'data' in response:
            id_key = response['data'][0].get(self.ID_KEY)
        else:
            id_key = response.get('email')
        if not id_key:
            log.error("ID_KEY is not found in the User data response. SSO won't work correctly")
        return id_key