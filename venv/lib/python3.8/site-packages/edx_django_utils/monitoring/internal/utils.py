"""
Defines several custom monitoring helpers, some of which work with
the CachedCustomMonitoringMiddleware.

Usage:

    from edx_django_utils.monitoring import accumulate
    ...
    accumulate('xb_user_state.get_many.num_items', 4)

There is no need to do anything else.  The custom attributes are automatically
cleared before the next request.

We try to keep track of our custom monitoring at:
https://openedx.atlassian.net/wiki/spaces/PERF/pages/54362736/Custom+Attributes+in+New+Relic

At this time, the custom monitoring will only be reported to New Relic.

"""
from .middleware import CachedCustomMonitoringMiddleware

try:
    import newrelic.agent
except ImportError:  # pragma: no cover
    newrelic = None  # pylint: disable=invalid-name


def accumulate(name, value):
    """
    Accumulate monitoring custom attribute for the current request.

    The named attribute is accumulated by a numerical amount using the sum.  All
    attributes are queued up in the request_cache for this request.  At the end of
    the request, the monitoring_utils middleware will batch report all
    queued accumulated attributes to the monitoring tool (e.g. New Relic).

    Arguments:
        name (str): The attribute name.  It should be period-delimited, and
            increase in specificity from left to right.  For example:
            'xb_user_state.get_many.num_items'.
        value (number):  The amount to accumulate into the named attribute.  When
            accumulate() is called multiple times for a given attribute name
            during a request, the sum of the values for each call is reported
            for that attribute.  For attributes which don't make sense to accumulate,
            use ``set_custom_attribute`` instead.

    """
    CachedCustomMonitoringMiddleware.accumulate_attribute(name, value)


def increment(name):
    """
    Increment a monitoring custom attribute representing a counter.

    Here we simply accumulate a new custom attribute with a value of 1, and the
    middleware should automatically aggregate this attribute.
    """
    accumulate(name, 1)


def set_custom_attributes_for_course_key(course_key):
    """
    Set monitoring custom attributes related to a course key.

    This is not cached, and only support reporting to New Relic Insights.

    """
    if newrelic:  # pragma: no cover
        newrelic.agent.add_custom_parameter('course_id', str(course_key))
        newrelic.agent.add_custom_parameter('org', str(course_key.org))


def set_custom_attribute(key, value):
    """
    Set monitoring custom attribute.

    This is not cached, and only support reporting to New Relic Insights.

    """
    if newrelic:  # pragma: no cover
        # note: parameter is new relic's older name for attributes
        newrelic.agent.add_custom_parameter(key, value)


def record_exception():
    """
    Records a caught exception to the monitoring system.

    Note: By default, only unhandled exceptions are monitored. This function
    can be called to record exceptions as monitored errors, even if you handle
    the exception gracefully from a user perspective.

    For more details, see:
    https://docs.newrelic.com/docs/agents/python-agent/python-agent-api/recordexception-python-agent-api

    """
    if newrelic:  # pragma: no cover
        newrelic.agent.record_exception()
