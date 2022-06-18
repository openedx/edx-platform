from .oauth import BaseOAuth2


class CILogonOAuth2(BaseOAuth2):
    """
    CI Logon Authentication Backend

    Docs: https://www.cilogon.org/oidc
    """

    name = 'cilogon-oauth2'
    AUTHORIZATION_URL = 'https://cilogon.org/authorize'
    ACCESS_TOKEN_URL = 'https://cilogon.org/oauth2/token'
    ACCESS_TOKEN_METHOD = 'POST'
    DEFAULT_SCOPE = ['openid', 'email', 'profile', 'org.cilogon.userinfo']
    REDIRECT_STATE = False
    SCOPE_SEPARATOR = '+'

    def user_data(self, token, *args, **kwargs):
        """Loads user data from endpoint"""
        url = 'https://cilogon.org/oauth2/userinfo'
        data = {'access_token': token}
        try:
            return self.get_json(url, method='POST', data=data)
        except ValueError:
            return None
    
    def get_user_id(self, details, response):
        """Return user unique id provided by service
           In this case it is a combination of the `sub`
           and `iss` respective values."""
        return response.get('sub', '') + ' ' + response.get('iss', '')

    def get_user_details(self, response):
        """Return user details from CI Logon service"""
        fullname, first_name, last_name = self.get_user_names(
            first_name=response.get('given_name'),
            last_name=response.get('family_name')
        )
        return {
            'username': response.get('email'),
            'email': response.get('email'),
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
        }
