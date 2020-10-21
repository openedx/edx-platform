"""
PhilU custom auth backends
"""
from social_core.backends.facebook import FacebookOAuth2
from social_core.backends.google import GoogleOAuth2
from social_core.backends.linkedin import LinkedinOAuth2
from social_core.exceptions import AuthCanceled


# TODO: Remove this when edx version is upgraded to ironwood/hawthorne
class CustomFacebookOAuth(FacebookOAuth2):  # pylint: disable=abstract-method
    REDIRECT_STATE = False


# TODO: Remove this when edx version is upgraded to ironwood/hawthorne
class CustomGoogleOAuth(GoogleOAuth2):  # pylint: disable=abstract-method
    """
    Custom Google OAuth Backend
    """

    def get_user_id(self, details, response):
        """Use google email as unique id"""
        if self.setting('USE_UNIQUE_USER_ID', False):
            if 'sub' in response:
                return response['sub']
            else:
                return response['id']
        else:
            return details['email']

    def get_user_details(self, response):
        """Return user details from Google API account"""
        if 'email' in response:
            email = response['email']
        else:
            email = ''

        name, given_name, family_name = (
            response.get('name', ''),
            response.get('given_name', ''),
            response.get('family_name', ''),
        )

        fullname, first_name, last_name = self.get_user_names(
            name, given_name, family_name
        )
        return {'username': email.split('@', 1)[0],
                'email': email,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name}

    def user_data(self, access_token, *args, **kwargs):
        """Return user data from Google API"""
        return self.get_json(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            params={
                'access_token': access_token,
                'alt': 'json'
            }
        )


# LinkedinOauth has been customized and updated from the latest version of python-social-auth. This was done because
# updating the package in question breaks other packages' dependencies.
# TODO: Remove this when edx version is upgraded to ironwood/hawthorne
class CustomLinkedinOAuth(LinkedinOAuth2):  # pylint: disable=abstract-method
    """
    Custom LinkedIn OAuth Backend
    """
    AUTHORIZATION_URL = \
        'https://www.linkedin.com/oauth/v2/authorization'
    ACCESS_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
    USER_DETAILS_URL = \
        'https://api.linkedin.com/v2/me?projection=({projection})'
    USER_EMAILS_URL = 'https://api.linkedin.com/v2/emailAddress' \
                      '?q=members&projection=(elements*(handle~))'
    DEFAULT_SCOPE = ['r_liteprofile']
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires_in', 'expires'),
        ('firstName', 'first_name'),
        ('lastName', 'last_name')
    ]

    def user_details_url(self):
        # use set() since LinkedIn fails when values are duplicated
        fields_selectors = list(set(['id', 'firstName', 'lastName'] +
                                    self.setting('FIELD_SELECTORS', [])))
        # user sort to ease the tests URL mocking
        fields_selectors.sort()
        fields_selectors = ','.join(fields_selectors)
        return self.USER_DETAILS_URL.format(projection=fields_selectors)

    def user_emails_url(self):
        return self.USER_EMAILS_URL

    def user_data(self, access_token, *args, **kwargs):
        response = self.get_json(
            self.user_details_url(),
            headers=self.user_data_headers(access_token)
        )

        if 'emailAddress' in set(self.setting('FIELD_SELECTORS', [])):
            emails = self.email_data(access_token, *args, **kwargs)
            if emails:
                response['emailAddress'] = emails[0]

        return response

    def email_data(self, access_token, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get user email data from LinkedIn
        """
        response = self.get_json(
            self.user_emails_url(),
            headers=self.user_data_headers(access_token)
        )
        email_addresses = []
        for element in response.get('elements', []):
            email_address = element.get('handle~', {}).get('emailAddress')
            email_addresses.append(email_address)
        return list(filter(None, email_addresses))

    def get_user_details(self, response):
        """Return user details from Linkedin account"""

        def get_localized_name(name):
            """
            FirstName & Last Name object
            {
                  "localized":{
                     "en_US":"Smith"
                  },
                  "preferredLocale":{
                     "country":"US",
                     "language":"en"
                  }
            }
            :return the localizedName from the lastName object
            """
            locale = "{}_{}".format(
                name["preferredLocale"]["language"],
                name["preferredLocale"]["country"]
            )
            return name['localized'].get(locale, '')

        fullname, first_name, last_name = self.get_user_names(
            first_name=get_localized_name(response['firstName']),
            last_name=get_localized_name(response['lastName'])
        )
        email = response.get('emailAddress', '')
        return {'username': first_name + last_name,
                'fullname': fullname,
                'first_name': first_name,
                'last_name': last_name,
                'email': email}

    def user_data_headers(self, access_token):  # pylint: disable=arguments-differ
        headers = {}
        lang = self.setting('FORCE_PROFILE_LANGUAGE')
        if lang:
            headers['Accept-Language'] = lang if lang is not True \
                else self.strategy.get_language()
        headers['Authorization'] = 'Bearer {access_token}'.format(
            access_token=access_token)
        return headers

    def process_error(self, data):
        super(CustomLinkedinOAuth, self).process_error(data)
        if data.get('serviceErrorCode'):
            raise AuthCanceled(self, data.get('message') or data.get('status'))
