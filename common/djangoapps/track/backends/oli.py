"""OLI analytics service event tracker backend."""

from __future__ import absolute_import

import json
import logging

import requests
from requests.exceptions import RequestException

from django.contrib.auth.models import User

from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_by_id
from student.models import anonymous_id_for_user
from track.backends import BaseBackend


log = logging.getLogger(__name__)


class OLIAnalyticsBackend(BaseBackend):

    def __init__(self, **kwargs):
        super(OLIAnalyticsBackend, self).__init__(**kwargs)

        self.path = kwargs.get('path', '')

    def send(self, event):
        """Forward the event to the OLI analytics server"""

        if event.get('event_type', '') != 'problem_check':
            return

        if event.get('event_source', '') != 'server':
            return

        context = event.get('context')
        if not context:
            return

        course_id = context.get('course_id')
        if not course_id:
            return

        course_key = CourseKey.from_string(course_id)
        course = get_course_by_id(course_key)

        if not course or not course.oli_analytics_service_url or not course.oli_analytics_service_secret:
            return

        user_id = context.get('user_id')
        if not user_id:
            return

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return

        event_data = event.get('event', {})
        if not event_data:
            return

        problem_id = event_data.get('problem_id')
        if not problem_id:
            return

        success = event_data.get('success')
        if not success:
            return

        is_correct = success == 'correct'

        payload = {
            'course_id': course_id,
            'resource_id': problem_id,
            'student_id': self._get_student_id(user),
            'result': is_correct
        }
        headers = {
            'Authorization': self._get_authorization_header(course.oli_analytics_service_secret)
        }

        request_payload_string = json.dumps({'payload': json.dumps(payload)})
        request_payload = {'request': request_payload_string}
        endpoint = course.oli_analytics_service_url + self.path
        try:
            log.info(endpoint)
            log.info(request_payload_string)
            response = requests.put(
                endpoint,
                data=request_payload,
                timeout=course.oli_analytics_service_timeout,
                headers=headers
            )
            response.raise_for_status()
            log.info(response.text)
        except RequestException:
            log.warning('Unable to send event to OLI analytics service', exc_info=True)

    def _get_student_id(self, user):
        return anonymous_id_for_user(user, None)

    def _get_authorization_header(self, secret):
        return secret
