"""Handle events that were forwarded from the segment.io webhook integration"""

import datetime
import json
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django_future.csrf import csrf_exempt

from eventtracking import tracker as eventtracker
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from util.json_request import expect_json, JsonResponse

from track import tracker
from track import shim

log = logging.getLogger(__name__)


ERROR_UNAUTHORIZED = 'Unauthorized'
WARNING_IGNORED_CHANNEL = 'Channel ignored'
WARNING_IGNORED_ACTION = 'Action ignored'
ERROR_MISSING_USER_ID = 'Required user_id missing from context'
ERROR_USER_NOT_EXIST = 'Specified user does not exist'
ERROR_INVALID_USER_ID = 'Unable to parse userId as an integer'
ERROR_MISSING_EVENT_TYPE = 'The event_type field must be specified in the properties dictionary'
ERROR_MISSING_TIMESTAMP = 'Required timestamp field not found'
ERROR_MISSING_RECEIVED_AT = 'Required receivedAt field not found'


@require_POST
@expect_json
@csrf_exempt
def track_segmentio_event(request):
    """
    An endpoint for logging events using segment.io's webhook integration.

    segment.io provides a custom integration mechanism that initiates a request to a configurable URL every time an
    event is received by their system. This endpoint is designed to receive those requests and convert the events into
    standard tracking log entries.

    For now we limit the scope of handled events to track and screen events from mobile devices. In the future we could
    enable logging of other types of events, however, there is significant overlap with our non-segment.io based event
    tracking. Given that segment.io is closed third party solution we are limiting its required usage to just
    collecting events from mobile devices for the time being.

    Many of the root fields of a standard edX tracking event are read out of the "properties" dictionary provided by the
    segment.io event, which is, in turn, provided by the client that emitted the event.

    In order for an event to be logged the following preconditions must be met:

    * The "key" query string parameter must exactly match the django setting TRACKING_SEGMENTIO_WEBHOOK_SECRET. While
      the endpoint is public, we want to limit access to it to the segment.io servers only.
    * The value of the "channel" field of the event must be included in the list specified by the django setting
      TRACKING_SEGMENTIO_ALLOWED_CHANNELS. This is intended to restrict the set of events to specific channels. For
      example: just mobile devices.
    * The value of the "action" field of the event must be included in the list specified by the django setting
      TRACKING_SEGMENTIO_ALLOWED_ACTIONS. In order to make use of *all* of the features segment.io offers we would have
      to implement some sort of persistent storage of information contained in some actions (like identify). For now,
      we defer support of those actions and just support a limited set that can be handled without storing information
      in external state.
    * The value of the standard "userId" field of the event must be an integer that can be used to look up the user
      using the primary key of the User model.
    * Include an "event_type" field in the properties dictionary that indicates the edX event type. Note this can differ
      from the "event" field found in the root of a segment.io event. The "event" field at the root of the structure is
      intended to be human readable, the "event_type" field is expected to conform to the standard for naming events
      found in the edX data documentation.

    Additionally the event can optionally:

    * Provide a "context" dictionary in the properties dictionary. This dictionary will be applied to the
      existing context on the server overriding any existing keys. This context dictionary should include a "course_id"
      field when the event is scoped to a particular course. The value of this field should be a valid course key. The
      context may contain other arbitrary data that will be logged with the event, for example: identification
      information for the device that emitted the event.
    * Provide a "page" parameter in the properties dictionary which indicates the page that was being displayed to the
      user or the mobile application screen that was visible to the user at the time the event was emitted.

    """

    # Validate the security token. We must use a query string parameter for this since we cannot customize the POST body
    # in the segment.io webhook configuration, we can only change the URL that they call, so we force this token to be
    # included in the URL and reject any requests that do not include it. This also assumes HTTPS is used to make the
    # connection between their server and ours.
    expected_secret = getattr(settings, 'TRACKING_SEGMENTIO_WEBHOOK_SECRET', None)
    provided_secret = request.GET.get('key')
    if not expected_secret or provided_secret != expected_secret:
        return failure_response(ERROR_UNAUTHORIZED, status=401)

    # The POST body will contain the JSON encoded event
    full_segment_event = request.json

    def logged_failure_response(*args, **kwargs):
        """Indicate a failure and log information about the event that will aide debugging efforts"""
        failed_response = failure_response(*args, **kwargs)
        log.warning('Unable to process event received from segment.io: %s', json.dumps(full_segment_event))
        return failed_response

    # Selectively listen to particular channels
    channel = full_segment_event.get('channel')
    allowed_channels = [c.lower() for c in getattr(settings, 'TRACKING_SEGMENTIO_ALLOWED_CHANNELS', [])]
    if not channel or channel.lower() not in allowed_channels:
        return response(WARNING_IGNORED_CHANNEL, committed=False)

    # Ignore actions that are unsupported
    action = full_segment_event.get('action')
    allowed_actions = [a.lower() for a in getattr(settings, 'TRACKING_SEGMENTIO_ALLOWED_ACTIONS', [])]
    if not action or action.lower() not in allowed_actions:
        return response(WARNING_IGNORED_ACTION, committed=False)

    # We mostly care about the properties
    segment_event = full_segment_event.get('properties', {})

    context = {}

    # Start with the context provided by segment.io in the "client" field if it exists
    segment_context = full_segment_event.get('context')
    if segment_context:
        context['client'] = segment_context

    # Overlay any context provided in the properties
    context.update(segment_event.get('context', {}))

    user_id = full_segment_event.get('userId')
    if not user_id:
        return logged_failure_response(ERROR_MISSING_USER_ID)

    # userId is assumed to be the primary key of the django User model
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return logged_failure_response(ERROR_USER_NOT_EXIST)
    except ValueError:
        return logged_failure_response(ERROR_INVALID_USER_ID)
    else:
        context['user_id'] = user_id

    # course_id is expected to be provided in the context when applicable
    course_id = context.get('course_id')
    if course_id:
        try:
            course_key = CourseKey.from_string(course_id)
            context['org_id'] = course_key.org
        except InvalidKeyError:
            log.warning(
                'unable to parse course_id "{course_id}" from event: {event}'.format(
                    course_id=course_id,
                    event=json.dumps(full_segment_event),
                ),
                exc_info=True
            )

    if 'timestamp' in full_segment_event:
        time = parse_iso8601_timestamp(full_segment_event['timestamp'])
    else:
        return logged_failure_response(ERROR_MISSING_TIMESTAMP)

    if 'receivedAt' in full_segment_event:
        context['received_at'] = parse_iso8601_timestamp(full_segment_event['receivedAt'])
    else:
        return logged_failure_response(ERROR_MISSING_RECEIVED_AT)

    if 'event_type' in segment_event:
        event_type = segment_event['event_type']
    else:
        return logged_failure_response(ERROR_MISSING_EVENT_TYPE)

    with eventtracker.get_tracker().context('edx.segmentio', context):
        complete_context = eventtracker.get_tracker().resolve_context()
        event = {
            "username": user.username,
            "event_type": event_type,
            # Will be either "mobile", "browser" or "server". These names happen to be identical to the names we already
            # use so no mapping is necessary.
            "event_source": channel,
            # This timestamp is reported by the local clock on the device so it may be wildly incorrect.
            "time": time,
            "context": complete_context,
            "page": segment_event.get('page'),
            "host": complete_context.get('host', ''),
            "agent": '',
            "ip": segment_event.get('ip', ''),
            "event": segment_event.get('event', {}),
        }

    # Some duplicated fields are passed into event-tracking via the context by track.middleware.
    # Remove them from the event here since they are captured elsewhere.
    shim.remove_shim_context(event)

    tracker.send(event)

    return response()


def response(message=None, status=200, committed=True):
    """
    Produce a response from the segment.io event handler.

    Returns: A JSON encoded string giving more information about what action was taken while processing the request.
    """
    result = {
        'committed': committed
    }

    if message:
        result['message'] = message

    return JsonResponse(result, status=status)


def failure_response(message, status=400):
    """
    Return a failure response when something goes wrong handling segment.io events.

    Returns: A JSON encoded string giving more information about what went wrong when processing the request.
    """
    return response(message=message, status=status, committed=False)


def parse_iso8601_timestamp(timestamp):
    """Parse a particular type of ISO8601 formatted timestamp"""
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
