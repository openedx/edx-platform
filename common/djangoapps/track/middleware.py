import hmac
import hashlib
import json
import re
import logging

from django.conf import settings

from track import views
from track import contexts
from eventtracking import tracker


log = logging.getLogger(__name__)

CONTEXT_NAME = 'edx.request'
META_KEY_TO_CONTEXT_KEY = {
    'REMOTE_ADDR': 'ip',
    'SERVER_NAME': 'host',
    'HTTP_USER_AGENT': 'agent',
    'PATH_INFO': 'path'
}


class TrackMiddleware(object):
    """
    Tracks all requests made, as well as setting up context for other server
    emitted events.
    """

    def process_request(self, request):
        try:
            self.enter_request_context(request)

            if not self.should_process_request(request):
                return

            # Removes passwords from the tracking logs
            # WARNING: This list needs to be changed whenever we change
            # password handling functionality.
            #
            # As of the time of this comment, only 'password' is used
            # The rest are there for future extension.
            #
            # Passwords should never be sent as GET requests, but
            # this can happen due to older browser bugs. We censor
            # this too.
            #
            # We should manually confirm no passwords make it into log
            # files when we change this.

            censored_strings = ['password', 'newpassword', 'new_password',
                                'oldpassword', 'old_password']
            post_dict = dict(request.POST)
            get_dict = dict(request.GET)
            for string in censored_strings:
                if string in post_dict:
                    post_dict[string] = '*' * 8
                if string in get_dict:
                    get_dict[string] = '*' * 8

            event = {'GET': dict(get_dict),
                      'POST': dict(post_dict)}

            # TODO: Confirm no large file uploads
            event = json.dumps(event)
            event = event[:512]

            views.server_track(request, request.META['PATH_INFO'], event)
        except:
            pass

    def should_process_request(self, request):
        """Don't track requests to the specified URL patterns"""
        path = request.META['PATH_INFO']

        ignored_url_patterns = getattr(settings, 'TRACKING_IGNORE_URL_PATTERNS', [])
        for pattern in ignored_url_patterns:
            # Note we are explicitly relying on python's internal caching of
            # compiled regular expressions here.
            if re.match(pattern, path):
                return False
        return True

    def enter_request_context(self, request):
        """
        Extract information from the request and add it to the tracking
        context.

        The following fields are injected into the context:

        * session - The Django session key that identifies the user's session.
        * user_id - The numeric ID for the logged in user.
        * username - The username of the logged in user.
        * ip - The IP address of the client.
        * host - The "SERVER_NAME" header, which should be the name of the server running this code.
        * agent - The client browser identification string.
        * path - The path part of the requested URL.
        * client_id - The unique key used by Google Analytics to identify a user
        """
        context = {
            'session': self.get_session_key(request),
            'user_id': self.get_user_primary_key(request),
            'username': self.get_username(request),
        }
        for header_name, context_key in META_KEY_TO_CONTEXT_KEY.iteritems():
            context[context_key] = request.META.get(header_name, '')

        # Google Analytics uses the clientId to keep track of unique visitors. A GA cookie looks like 
        # this: _ga=GA1.2.1033501218.1368477899. The clientId is this part: 1033501218.1368477899.
        google_analytics_cookie = request.COOKIES.get('_ga')
        if google_analytics_cookie is None:
            context['client_id'] = None
        else:
            context['client_id'] = '.'.join(google_analytics_cookie.split('.')[2:])

        context.update(contexts.course_context_from_url(request.build_absolute_uri()))

        tracker.get_tracker().enter_context(
            CONTEXT_NAME,
            context
        )

    def get_session_key(self, request):
        """ Gets and encrypts the Django session key from the request or an empty string if it isn't found."""
        try:
            return self.encrypt_session_key(request.session.session_key)
        except AttributeError:
            return ''

    def encrypt_session_key(self, session_key):
        """Encrypts a Django session key to another 32-character hex value."""
        if not session_key:
            return ''

        # Follow the model of django.utils.crypto.salted_hmac() and
        # django.contrib.sessions.backends.base._hash() but use MD5
        # instead of SHA1 so that the result has the same length (32)
        # as the original session_key.
        key_salt = "common.djangoapps.track" + self.__class__.__name__
        key = hashlib.md5(key_salt + settings.SECRET_KEY).digest()
        encrypted_session_key = hmac.new(key, msg=session_key, digestmod=hashlib.md5).hexdigest()
        return encrypted_session_key

    def get_user_primary_key(self, request):
        """Gets the primary key of the logged in Django user"""
        try:
            return request.user.pk
        except AttributeError:
            return ''

    def get_username(self, request):
        """Gets the username of the logged in Django user"""
        try:
            return request.user.username
        except AttributeError:
            return ''

    def process_response(self, _request, response):
        """Exit the context if it exists."""
        try:
            tracker.get_tracker().exit_context(CONTEXT_NAME)
        except Exception:  # pylint: disable=broad-except
            pass

        return response
