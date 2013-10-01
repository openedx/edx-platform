"""
Defines shim classes necessary to support the "old" event format.
"""

from __future__ import absolute_import

import json

from track.views import server_track


class LegacyShimBackend(object):
    """
    A shim backend that generates events in the legacy format.  For this to
    work the event must include all fields that are used by the legacy format.
    The legacy event field set must be a subset of the new field set.  This
    restricts the contents of new events somewhat in order to support these
    deprecated events.
    """

    def send(self, event):
        """Forward the event to the legacy tracking system"""
        event_type = event['event_type']
        context = event['context']
        data = event['data']

        if event_type == 'edx.http.request':
            event_data = json.dumps({
                'GET': data.get('query', {}),
                'POST': data.get('body', {}),
            })
            event_data = event_data[:512]
            server_track(
                FakeRequest(context),
                context.get('path', ''),
                event_data
            )


class FakeRequest(object):
    """
    A dummy request object since the legacy event tracking system reads
    information directly from the request, since this backend does not have
    access to the request, it instead constructs a fake request with all of
    the requisite data.
    """

    def __init__(self, context):
        self.user = FakeUser(context.get('username', ''))
        self.META = {
            'HTTP_USER_AGENT': context.get('agent', ''),
            'REMOTE_ADDR': context.get('ip', ''),
            'SERVER_NAME': context.get('host', '')
        }


class FakeUser(object):
    """
    In order to support request.user.username queries on the fake request
    object, we also construct a fake user object.
    """

    def __init__(self, username):
        self.username = username