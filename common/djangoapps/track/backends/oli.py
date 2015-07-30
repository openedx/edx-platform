"""
OLI analytics service event tracker backend.
"""
from __future__ import absolute_import

import json
import logging
from urlparse import urljoin

from django.contrib.auth.models import User
from requests_oauthlib import OAuth1Session

from student.models import anonymous_id_for_user
from track.backends import BaseBackend


LOG = logging.getLogger(__name__)


class OLIAnalyticsBackend(BaseBackend):
    """
    Transmit events to the OLI analytics service
    """
    def __init__(
            self,
            url=None,
            path=None,
            key=None,
            secret=None,
            course_ids=None,
            **kwargs
    ):
        super(OLIAnalyticsBackend, self).__init__(**kwargs)

        self.url = url
        self.path = path
        self.key = key
        self.secret = secret

        # only courses with id in this set will have their data sent
        self.course_ids = set()
        if course_ids is not None:
            self.course_ids = set(course_ids)

        self.oauth = OAuth1Session(self.key, client_secret=self.secret)

    def send(self, event):
        """
        Forward the event to the OLI analytics server
        Exact API here: https://docs.google.com/document/d/1ZB-qwP0bV7ko_xJdJNX1PYKvTyYd4I8CBltfac4dlfw/edit?pli=1#
        OAuth 1 with nonce and body signing
        """
        if not (self.url and self.secret and self.key):
            return None

        # Only currently passing problem_check events, which are CAPA only
        if event.get('event_type') != 'problem_check':
            return None

        if event.get('event_source') != 'server':
            return None

        context = event.get('context')
        if not context:
            return None

        course_id = context.get('course_id')
        if not course_id or course_id not in self.course_ids:
            return None

        user_id = context.get('user_id')
        if not user_id:
            return None

        event_data = event.get('event')
        if not event_data:
            return None

        problem_id = event_data.get('problem_id')
        if not problem_id:
            return None

        success = event_data.get('success')
        if not success:
            return None

        is_correct = success == 'correct'

        # put the most expensive operation (DB access) at the end, to not do it needlessly
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            LOG.warning('Can not find a user with user_id: %s', user_id)
            return None

        payload = {
            'course_id': course_id,
            'resource_id': problem_id,
            'student_id': anonymous_id_for_user(user, None),
            'result': is_correct,
        }

        request_payload_string = json.dumps({'payload': json.dumps(payload)})
        request_payload = {'request': request_payload_string}
        endpoint = urljoin(self.url, self.path)
        try:
            response = self.oauth.put(endpoint, request_payload)

            # Note: CourseBuilder's API always returns status_code=200, regardless of the actual error,
            # so response.status_code is misleading.
            # You should check the actual contents of the response.
            # The response body will look like {"status":200, "message":"OK", "payload": .....}.

            # Because Google prepends ')]}'\n to all json responses, to protect
            # against XSSI (cross-site-scripting-inclusion), need to reformat the
            # returned payloads

            message = json.loads(response.content.split('\n')[-1])
            if message['status'] == 200:
                return 'OK'
            else:
                LOG.warning('OLI analytics service returns error status: %s.', message)
                return 'Error'
        except Exception as error:
            LOG.warning(
                "Unable to send event to OLI analytics service: %s: %s: %s",
                endpoint,
                payload,
                error,
            )
            return None
