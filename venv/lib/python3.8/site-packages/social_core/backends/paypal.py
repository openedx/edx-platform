import base64

from .oauth import BaseOAuth2


class PayPalOAuth2(BaseOAuth2):
    """
    PayPal OAuth2 backend, docs at:
        https://developer.paypal.com/docs/connect-with-paypal/integrate/
    """

    name = 'paypal-oauth2'
    ID_KEY = 'user_id'
    AUTHORIZATION_URL = 'https://www.paypal.com/connect'
    ACCESS_TOKEN_URL = 'https://api.paypal.com/v1/oauth2/token'
    USER_DATA_URL = (
        'https://api.paypal.com/v1/identity/oauth2/userinfo?schema=paypalv1.1'
    )
    DEFAULT_SCOPE = ['openid', 'profile']
    ACCESS_TOKEN_METHOD = 'POST'
    REFRESH_TOKEN_METHOD = 'POST'
    REDIRECT_STATE = False

    def user_data(self, access_token, *args, **kwargs):
        auth_header = {'Authorization': 'Bearer %s' % access_token}
        response = self.get_json(self.USER_DATA_URL, headers=auth_header)
        return response

    def get_user_details(self, response):
        username = response.get(self.ID_KEY).split('/')[-1]
        fullname, first_name, last_name = self.get_user_names(
            response.get('name', ''),
            response.get('given_name', ''),
            response.get('family_name', ''),
        )
        emails = response.get('emails', [])
        email = self.get_email(emails)
        return {
            'username': username,
            'email': email,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
        }

    def auth_complete_params(self, state=None):
        return {
            'grant_type': 'authorization_code',
            'code': self.data.get('code', ''),
        }

    def auth_headers(self):
        auth = ('%s:%s' % self.get_key_and_secret()).encode()
        return {'Authorization': b'Basic ' + base64.urlsafe_b64encode(auth)}

    def refresh_token_params(self, token, *args, **kwargs):
        return {'refresh_token': token, 'grant_type': 'refresh_token'}

    @staticmethod
    def get_email(emails):
        if not emails:
            return ''
        primary_emails = (email for email in emails
                          if email.get('primary', False))
        primary_or_first = next(primary_emails, emails[0])
        return primary_or_first.get('value')


class PayPalOAuth2Sandbox(PayPalOAuth2):
    name = 'paypal-oauth2-sandbox'
    AUTHORIZATION_URL = 'https://www.sandbox.paypal.com/connect'
    ACCESS_TOKEN_URL = 'https://api.sandbox.paypal.com/v1/oauth2/token'
    USER_DATA_URL = (
        'https://api.sandbox.paypal.com/v1/identity/oauth2/userinfo?schema=paypalv1.1'
    )
