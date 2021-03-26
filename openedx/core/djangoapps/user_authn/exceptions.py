""" User Authn related Exceptions. """


from openedx.core.djangolib.markup import Text


class AuthFailedError(Exception):
    """
    This is a helper for the login view, allowing the various sub-methods to error out with an appropriate failure
    message.
    """
    def __init__(  # lint-amnesty, pylint: disable=dangerous-default-value
        self, value=None, redirect=None, redirect_url=None, error_code=None, context={},
    ):
        super(AuthFailedError, self).__init__()  # lint-amnesty, pylint: disable=super-with-arguments
        self.value = Text(value)
        self.redirect = redirect
        self.redirect_url = redirect_url
        self.error_code = error_code
        self.context = context

    def get_response(self):
        """ Returns a dict representation of the error. """
        resp = {'success': False}
        for attr in ('value', 'redirect', 'redirect_url', 'error_code', 'context'):
            if self.__getattribute__(attr):
                resp[attr] = self.__getattribute__(attr)

        return resp
