""" User Authn related Exceptions. """


class AuthFailedError(Exception):
    """
    This is a helper for the login view, allowing the various sub-methods to early out with an appropriate failure
    message.
    """
    def __init__(self, value=None, redirect=None, redirect_url=None):
        super(AuthFailedError, self).__init__()
        self.value = value
        self.redirect = redirect
        self.redirect_url = redirect_url

    def get_response(self):
        """ Returns a dict representation of the error. """
        resp = {'success': False}
        for attr in ('value', 'redirect', 'redirect_url'):
            if self.__getattribute__(attr):
                resp[attr] = self.__getattribute__(attr)

        return resp
