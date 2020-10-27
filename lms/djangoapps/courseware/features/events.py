# pylint: disable=missing-docstring

from django.conf import settings
from lettuce import before, step, world
from pymongo import MongoClient

from openedx.core.lib.tests.tools import assert_equals, assert_in  # pylint: disable=no-name-in-module

REQUIRED_EVENT_FIELDS = [
    'agent',
    'event',
    'event_source',
    'event_type',
    'host',
    'ip',
    'page',
    'time',
    'username'
]


@before.all  # pylint: disable=no-member
def connect_to_mongodb():
    world.mongo_client = MongoClient(host=settings.MONGO_HOST, port=settings.MONGO_PORT_NUM)
    world.event_collection = world.mongo_client['track']['events']


@before.each_scenario  # pylint: disable=no-member
def reset_captured_events(_scenario):
    world.event_collection.drop()


@before.outline  # pylint: disable=no-member
def reset_between_outline_scenarios(_scenario, _order, _outline, _reasons_to_fail):
    world.event_collection.drop()


@step(r'[aA]n? course url "(.*)" event is emitted$')
def course_url_event_is_emitted(_step, url_regex):
    event_type = url_regex.format(world.scenario_dict['COURSE'].id)  # pylint: disable=no-member
    n_events_are_emitted(_step, 1, event_type, "server")


@step(r'([aA]n?|\d+) "(.*)" (server|browser) events? is emitted$')
def n_events_are_emitted(_step, count, event_type, event_source):

    # Ensure all events are written out to mongo before querying.
    world.mongo_client.fsync()

    # Note that splinter makes 2 requests when you call browser.visit('/foo')
    # the first just checks to see if the server responds with a status
    # code of 200, the next actually uses the browser to submit the request.
    # We filter out events associated with the status code checks by ignoring
    # events that come directly from splinter.
    criteria = {
        'event_type': event_type,
        'event_source': event_source,
        'agent': {
            '$ne': 'python/splinter'
        }
    }

    cursor = world.event_collection.find(criteria)

    try:
        number_events = int(count)
    except ValueError:
        number_events = 1

    assert_equals(cursor.count(), number_events)

    event = cursor.next()

    expected_field_values = {
        "username": world.scenario_dict['USER'].username,  # pylint: disable=no-member
        "event_type": event_type,
    }
    for key, value in expected_field_values.iteritems():
        assert_equals(event[key], value)

    for field in REQUIRED_EVENT_FIELDS:
        assert_in(field, event)
