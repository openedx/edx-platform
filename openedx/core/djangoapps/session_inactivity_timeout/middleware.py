"""
Middleware to auto-expire inactive sessions after N seconds, which is configurable in
settings.

To enable this feature, set in a settings.py:

  SESSION_INACTIVITY_TIMEOUT_IN_SECS = 300

This was taken from StackOverflow (http://stackoverflow.com/questions/14830669/how-to-expire-django-session-in-5minutes)

If left unset, session expiration will be handled by Django's SESSION_COOKIE_AGE,
which defaults to 1209600 (2 weeks, in seconds).
"""


from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.contrib import auth
from django.utils.deprecation import MiddlewareMixin

LAST_TOUCH_KEYNAME = 'SessionInactivityTimeout:last_touch'
LAST_SESSION_SAVE_TIME_KEYNAME = 'SessionInactivityTimeout:last_session_save_time'

LOG = logging.getLogger(__name__)

class SessionInactivityTimeout(MiddlewareMixin):
    """
    Middleware class to keep track of activity on a given session
    """
    def process_request(self, request):
        """
        Standard entry point for processing requests in Django
        """
        if not hasattr(request, "user") or not request.user.is_authenticated:
            #Can't log out if not logged in
            return

        timeout_in_seconds = getattr(settings, "SESSION_INACTIVITY_TIMEOUT_IN_SECONDS", None)

        # Do we have this feature enabled?
        if timeout_in_seconds:
            frequency_time_in_seconds = getattr(settings, "SESSION_SAVE_FREQUENCY_SECONDS", 60)
            # what time is it now?
            utc_now = datetime.utcnow()

            # Get the last time user made a request to server, which is stored in session data
            last_touch_str = request.session.get(LAST_TOUCH_KEYNAME)

            # have we stored a 'last visited' in session? NOTE: first time access after login
            # this key will not be present in the session data
            if last_touch_str:
                try:
                    # Convert the ISO string back to a datetime object
                    last_touch = datetime.fromisoformat(last_touch_str)

                    # compute the delta since last time user came to the server
                    time_since_last_activity = utc_now - last_touch

                    # did we exceed the timeout limit?
                    if time_since_last_activity > timedelta(seconds=timeout_in_seconds):
                        # yes? Then log the user out
                        del request.session[LAST_TOUCH_KEYNAME]
                        auth.logout(request)
                        return
                except (ValueError, TypeError) as e:
                    # If parsing fails, treat as if no timestamp exists
                    pass
            else:
                LOG.info("No previous activity timestamp found (first login)")

            # Store activity timestamp
            request.session[LAST_TOUCH_KEYNAME] = utc_now.isoformat()

            # Periodically allow a full save (every n seconds)
            last_save = request.session.get(LAST_SESSION_SAVE_TIME_KEYNAME)
            current_time = datetime.utcnow().isoformat()

            if not last_save or (
                datetime.fromisoformat(last_save) + timedelta(seconds=frequency_time_in_seconds) < datetime.utcnow()
            ):
                # Allow a full session save periodically
                request.session[LAST_SESSION_SAVE_TIME_KEYNAME] = current_time
                # Don't set modified=was_modified here! Let Django save the session
            else:
                # Only prevent saving in this branch
                request.session.modified = False
