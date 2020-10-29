"""
Custom authentication backends.
"""


from django.contrib.auth.backends import AllowAllUsersModelBackend as UserModelBackend
from ratelimitbackend.backends import RateLimitMixin


class EdxRateLimitedAllowAllUsersModelBackend(RateLimitMixin, UserModelBackend):
    """
    Authentication backend needed to incorporate rate limiting of login attempts - but also
    enabling users with is_active of False in the Django auth_user model to still authenticate.
    This is necessary for mobile users using 3rd party auth who have not activated their accounts,
    Inactive users who use 1st party auth (username/password auth) will still fail login attempts,
    just at a higher layer, in the login_user view.

    See: https://openedx.atlassian.net/browse/TNL-4516
    """
    pass
