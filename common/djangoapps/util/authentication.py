""" Common Authentication Handlers used across projects. """
from rest_framework import authentication


class SessionAuthenticationAllowInactiveUser(authentication.SessionAuthentication):
    """Ensure that the user is logged in, but do not require the account to be active.

    We use this in the special case that a user has created an account,
    but has not yet activated it.  We still want to allow the user to
    enroll in courses, so we remove the usual restriction
    on session authentication that requires an active account.

    You should use this authentication class ONLY for end-points that
    it's safe for an un-activated user to access.  For example,
    we can allow a user to update his/her own enrollments without
    activating an account.

    """
    def authenticate(self, request):
        """Authenticate the user, requiring a logged-in account and CSRF.

        This is exactly the same as the `SessionAuthentication` implementation,
        with the `user.is_active` check removed.

        Args:
            request (HttpRequest)

        Returns:
            Tuple of `(user, token)`

        Raises:
            PermissionDenied: The CSRF token check failed.

        """
        # Get the underlying HttpRequest object
        request = request._request  # pylint: disable=protected-access
        user = getattr(request, 'user', None)

        # Unauthenticated, CSRF validation not required
        # This is where regular `SessionAuthentication` checks that the user is active.
        # We have removed that check in this implementation.
        if not user:
            return None

        self.enforce_csrf(request)

        # CSRF passed with authenticated user
        return (user, None)
