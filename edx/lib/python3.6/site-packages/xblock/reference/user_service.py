"""
This file supports the XBlock service that returns data about users.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from xblock.reference.plugins import Service


class UserService(Service):
    """
    UserService returns information about users.  Initially only data about the currently-logged-in user.

    This service returns personally-identifiable information (PII).  If a runtime needed to control exposure to a
    user's PII, the runtime would deny access to this XBlock service.
    """
    def get_current_user(self):
        """
        This is default, example implementation.  Anything real needs to override

        This is expected to return an instance of XBlockUser
        """
        raise NotImplementedError()


class XBlockUser(object):
    """
    A model representation of user data returned by the `UserService`.

    There are two layers of fields for this class.  Standard user profile fields are first-class attributes
    of class instances.

    For an instance `xblock_user` of `XBlockUser`, the following fields will exist but may return None, except
    where a different "Falsey" default makes sense (which will be noted):
        - xblock_user.is_current_user:  is this user the current user of the xblock.  Always True for instances returned
          by `get_current_user()`
        - xblock_user.emails:  a list of email address for that user.  May return [] (in place of None)
        - xblock_user.full_name:  the full name of that user.  For example, used for generated certificates.
        - xblock_user.display_name:  the name of the user that should be shown in a display context.  The audience of
          display_name may be other users, as within a social-oriented xblock, or the user himself/herself,
          as in the top navigation bar of edx-platform.

    "Optional" user attributes are available under xblock_user.opt_attrs, which must support a dict-like interface.
    These user attributes are optional because they may be platform-specific or simply unavailable.  The `opt_attrs`
    field must exist for any instances of this class and be a dict-like thing, but none of its keys/values are
    guaranteed to exist, so using `.get()` or handling KeyError is recommended.  As an example, if the runtime is
    edx-platform:
        - xblock_user.opt_attrs['edx-platform.is_authenticated'] indicates whether the xblock_user is authenticated
          (e.g. not django's AnonymousUser)
        - xblock_user.opt_attrs['edx-platform.user_id'] is the edx-platform user id.
        - xblock_user.opt_attrs['edx-platform.username'] is the edx-platform username, which is used as the "handle"
          in discussion forums, for example.

    All of this data should be considered personally-identifiable information (PII).
    """
    def __init__(self, is_current_user=False, emails=None, full_name=None):
        # Set standardized attributes
        self.is_current_user = is_current_user
        self.emails = emails or []
        self.full_name = full_name
        self.opt_attrs = {}
