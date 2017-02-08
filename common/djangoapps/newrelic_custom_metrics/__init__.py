"""
This is an interface to the newrelic_custom_metrics middleware.  Functions
defined in this module can be used to report custom metrics to New Relic.  For
example:

    import newrelic_custom_metrics
    ...
    newrelic_custom_metrics.accumulate('xb_user_state.get_many.num_items', 4)

There is no need to do anything else.  The metrics are automatically cleared
before the next request.

We try to keep track of our custom metrics at:

https://openedx.atlassian.net/wiki/display/PERF/Custom+Metrics+in+New+Relic

TODO: supply additional public functions for storing strings and booleans.
"""

from newrelic_custom_metrics import middleware


def accumulate(name, value):
    """
    Accumulate custom New Relic metric for the current request.

    The named metric is accumulated by a numerical amount using the sum.  All
    metrics are queued up in the request_cache for this request.  At the end of
    the request, the newrelic_custom_metrics middleware will batch report all
    queued accumulated metrics to NR.

    Arguments:
        name (str): The metric name.  It should be period-delimited, and
            increase in specificty from left to right.  For example:
            'xb_user_state.get_many.num_items'.
        value (number):  The amount to accumulate into the named metric.  When
            accumulate() is called multiple times for a given metric name
            during a request, the sum of the values for each call is reported
            for that metric.  For metrics which don't make sense to accumulate,
            make sure to only call this function once during a request.
    """
    middleware.NewRelicCustomMetrics.accumulate_metric(name, value)


def increment(name):
    """
    Increment a custom New Relic metric representing a counter.

    Here we simply accumulate a new custom metric with a value of 1, and the
    middleware should automatically aggregate this metric.
    """
    accumulate(name, 1)
