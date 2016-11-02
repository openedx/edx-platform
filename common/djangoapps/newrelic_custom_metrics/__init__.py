"""
This is an interface to the newrelic_custom_metrics middleware.  Functions
defined in this module can be used to report custom metrics to New Relic.  For
example:

    import newrelic_custom_metrics
    ...
    newrelic_custom_metrics.accumulate('xb_user_state.get_many.num_items', 4)

There is no need to do anything else.  The metrics are automatically cleared
before the next request.
"""

from newrelic_custom_metrics import middleware


def accumulate(name, value):
    """
    Queue up a custom New Relic metric for the current request.  At the end of
    the request, the newrelic_custom_metrics middleware will batch report all
    queued metrics to NR.

    Q: What style of names should I use?
    A: Metric names should be comma delimited, becoming more specific from left
       to right.

    Q: What type can values be?
    A: numbers only.

    Q: What happens when I call this multiple times with the same name?
    A: Like-named metrics will be accumulated using the sum.
    """
    middleware.NewRelicCustomMetrics.accumulate_metric(name, value)


def increment(name):
    """
    Increment a custom New Relic metric representing a counter.

    Here we simply accumulate a new custom metric with a value of 1, and the
    middleware should automatically aggregate this metric.
    """
    accumulate(name, 1)
