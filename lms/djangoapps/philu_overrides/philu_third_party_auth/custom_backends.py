from social.backends.facebook import FacebookOAuth2
from social.backends.google import GoogleOAuth2


class CustomFacebookOAuth(FacebookOAuth2):
    REDIRECT_STATE = False


class CustomGoogleOAuth(GoogleOAuth2):

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
