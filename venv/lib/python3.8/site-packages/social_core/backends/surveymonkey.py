"""
SurveyMonkey OAuth2 backend, docs at:
    https://developer.surveymonkey.com/api/v3/#authentication
"""
from .oauth import BaseOAuth2


class SurveyMonkeyOAuth2(BaseOAuth2):
    """SurveyMonkey OAuth2 authentication backend"""
    name = 'surveymonkey'
    AUTHORIZATION_URL = 'https://api.surveymonkey.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://api.surveymonkey.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    USER_DATA_URL = '/v3/users/me'
    STATE_PARAMETER = False
    REDIRECT_STATE = False
    EXTRA_DATA = [
        ('access_url', 'access_url'),
    ]

    def get_user_details(self, response):
        """Return user details from a SurveyMonkey /users/me response"""
        response['name'] = response['first_name'] + ' ' + response['last_name']
        return response

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data information from service"""
        base_url = kwargs['response']['access_url']
        return self.get_json(base_url + self.USER_DATA_URL, headers={
          'Authorization': 'bearer ' + access_token
        })
