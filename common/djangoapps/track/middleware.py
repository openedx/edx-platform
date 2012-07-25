import json

from django.conf import settings

import views


class TrackMiddleware:
    def process_request(self, request):
        try:
            # We're already logging events, and we don't want to capture user
            # names/passwords.
            if request.META['PATH_INFO'] in ['/event', '/login']:
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
