"""
Middleware for handling the storage, aggregation, and reporing of custom New
Relic metrics.

This middleware will only call on the newrelic agent if there are any metrics
to report for this request, so it will not incur any processing overhead for
request handlers which do not record custom metrics.
"""
import newrelic.agent
import request_cache

REQUEST_CACHE_KEY = 'newrelic_custom_metrics'


class NewRelicCustomMetrics(object):
    """
    The middleware class.  Make sure to add below the request cache in
    MIDDLEWARE_CLASSES.
    """

    @classmethod
    def _get_metrics_cache(cls):
        """
        Get a reference to the part of the request cache wherein we store New
        Relic custom metrics related to the current request.
        """
        return request_cache.get_cache(name=REQUEST_CACHE_KEY)

    @classmethod
    def accumulate_metric(cls, name, value):
        """
        Accumulate a custom metric (name and value) in the metrics cache.
        """
        metrics_cache = cls._get_metrics_cache()
        metrics_cache.setdefault(name, 0)
        metrics_cache[name] += value

    @classmethod
    def _batch_report(cls):
        """
        Report the collected custom metrics to New Relic.
        """
        metrics_cache = cls._get_metrics_cache()
        for metric_name, metric_value in metrics_cache.iteritems():
            newrelic.agent.add_custom_parameter(metric_name, metric_value)

    # Whether or not there was an exception, report any custom NR metrics that
    # may have been collected.

    def process_response(self, request, response):  # pylint: disable=unused-argument
        """
        Django middleware handler to process a response
        """
        self._batch_report()
        return response

    def process_exception(self, request, exception):  # pylint: disable=unused-argument
        """
        Django middleware handler to process an exception
        """
        self._batch_report()
        return None
