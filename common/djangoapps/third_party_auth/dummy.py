"""
DummyBackend: A fake Third Party Auth provider for testing & development purposes.
"""


from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthFailed


class DummyBackend(BaseOAuth2):  # pylint: disable=abstract-method
    """
    python-social-auth backend that doesn't actually go to any third party site
    """
    name = "dummy"
    SUCCEED = True  # You can patch this during tests in order to control whether or not login works

    def auth_url(self):
        """ Get the URL to which we must redirect in order to authenticate the user """
        return self.redirect_uri

    def get_user_details(self, response):
        """ Get user details like full name, email, etc. from the third party """
        return {
            'fullname': "William Adama",
            'first_name': "Bill",
            'last_name': "Adama",
            'username': "Galactica1",
            'email': "adama@fleet.colonies.gov",
        }

    def get_user_id(self, details, response):
        """ Get the permanent ID for this user from the third party. """
        return '1234'

    def auth_complete(self, *args, **kwargs):
        """
        The user has been redirected back from the third party and we should now log them in, if
        everything checks out.
        """
        if not DummyBackend.SUCCEED:
            raise AuthFailed(self, 'Third Party login failed.')

        response = {
            'dummy': True,
        }

        kwargs.update({'response': response, 'backend': self})

        return self.strategy.authenticate(*args, **kwargs)
