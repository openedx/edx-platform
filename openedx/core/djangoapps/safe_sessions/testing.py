"""
Test overrides to support Safe Cookies with Test Clients.
"""


from django.test.client import Client


def safe_cookie_test_session_patch():
    """
    Override the Test Client's methods in order to support Safe Cookies.
    If there's a better way to patch this, we should do so.
    """
    if getattr(safe_cookie_test_session_patch, 'has_run', False):
        return

    def using_safe_cookie_data(settings):
        """
        Returns whether or not Safe Cookies is actually being
        used, by checking the middleware settings.
        """
        return (
            'openedx.core.djangoapps.safe_sessions.middleware.SafeSessionMiddleware' in settings.MIDDLEWARE
        )

    ## session_id --> safe_cookie_data ##

    # Override Client.login and force_login method to update cookies with safe
    # cookies.
    patched_client_login = Client.login
    patched_client_force_login = Client.force_login

    def login_with_safe_session(self, **credentials):
        """
        Call the original Client.login method, but update the
        session cookie with a freshly computed safe_cookie_data
        before returning.
        """
        from django.conf import settings
        from django.contrib.auth import SESSION_KEY
        from .middleware import SafeSessionMiddleware

        import pdb;
        pdb.set_trace()

        if not patched_client_login(self, **credentials):
            return False
        if using_safe_cookie_data(settings):
            SafeSessionMiddleware.update_with_safe_session_cookie(self.cookies, self.session[SESSION_KEY])
        return True
    Client.login = login_with_safe_session

    def force_login_with_safe_session(self, user, backend='openedx.core.djangoapps.oauth_dispatch.dot_overrides.backends.EdxRateLimitedAllowAllUsersModelBackend'):
        """
        Call the original Client.force_login method, but update the
        session cookie with a freshly computed safe_cookie_data
        before returning.
        """
        from django.conf import settings
        from django.contrib.auth import SESSION_KEY
        from .middleware import SafeSessionMiddleware

        patched_client_force_login(self, user, backend)

        if not hasattr(self.session, '_auth_user_id'):
            return False

        if using_safe_cookie_data(settings):
            SafeSessionMiddleware.update_with_safe_session_cookie(self.cookies, self.session[SESSION_KEY])
        return True
    Client.force_login = force_login_with_safe_session

    ## safe_cookie_data --> session_id ##

    # Override Client.session so any safe cookies are parsed before
    # use.
    def get_safe_session(self):
        """
        Here, we are duplicating the original Client._session code
        in order to allow conversion of the safe_cookie_data back
        to the raw session_id, if needed.  Since test code may
        access the session_id before it's actually converted,
        we use a try-except clause here to check both cases.
        """
        from django.apps import apps
        from django.conf import settings
        from importlib import import_module
        from .middleware import SafeCookieData, SafeCookieError, SafeSessionMiddleware

        if apps.is_installed('django.contrib.sessions'):
            engine = import_module(settings.SESSION_ENGINE)
            cookie = self.cookies.get(settings.SESSION_COOKIE_NAME, None)
            if cookie:
                session_id = cookie.value
                if using_safe_cookie_data(settings):
                    try:
                        session_id = SafeCookieData.parse(session_id).session_id
                    except SafeCookieError:
                        pass  # The safe cookie hasn't yet been created.
                return engine.SessionStore(session_id)
            else:
                session = engine.SessionStore()
                session.save()
                self.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
                SafeSessionMiddleware.update_with_safe_session_cookie(self.cookies, user_id=None)
                return session
        return {}
    Client.session = property(get_safe_session)

    safe_cookie_test_session_patch.has_run = True
