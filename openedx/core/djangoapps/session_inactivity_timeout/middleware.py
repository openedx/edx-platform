"""
Middleware to auto-expire inactive sessions after N seconds, which is configurable in
settings.

To enable this feature, set in a settings.py:

  SESSION_INACTIVITY_TIMEOUT_IN_SECS = 300

This was taken from StackOverflow (http://stackoverflow.com/questions/14830669/how-to-expire-django-session-in-5minutes)
"""
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import auth

LAST_TOUCH_KEYNAME = 'SessionInactivityTimeout:last_touch'


class SessionInactivityTimeout(object):
    """
    Middleware class to keep track of activity on a given session
    """
    def process_request(self, request):
        """
        Standard entry point for processing requests in Django
        """
        if not hasattr(request, "user") or not request.user.is_authenticated():
            #Can't log out if not logged in
            return

        timeout_in_seconds = getattr(settings, "SESSION_INACTIVITY_TIMEOUT_IN_SECONDS", None)

        # Do we have this feature enabled?
        if timeout_in_seconds:
            # what time is it now?
            utc_now = datetime.utcnow()

            # Get the last time user made a request to server, which is stored in session data
            last_touch = request.session.get(LAST_TOUCH_KEYNAME)

            # have we stored a 'last visited' in session? NOTE: first time access after login
            # this key will not be present in the session data
            if last_touch:
                # compute the delta since last time user came to the server
                time_since_last_activity = utc_now - last_touch

                # did we exceed the timeout limit?
                if time_since_last_activity > timedelta(seconds=timeout_in_seconds):
                    # yes? Then log the user out
                    del request.session[LAST_TOUCH_KEYNAME]
                    auth.logout(request)
                    return

            request.session[LAST_TOUCH_KEYNAME] = utc_now
