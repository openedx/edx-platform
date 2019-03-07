"""
Currently edx is using 1.7.0 version of social-auth-core
which uses google-plus-api to sign in with google.
As google plus is being shutting down on 7th of March,
so this version of social-auth-core will cause problems.
Luckily social-auth-core version 3.0.0 Link has handled
this issue already so this module is to incorporate that fix
into the edx code by adding custom google oauth2 backend for google+.
"""
from social_core.backends.google import GoogleOAuth2


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
