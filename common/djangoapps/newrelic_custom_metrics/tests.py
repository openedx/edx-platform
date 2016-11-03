"""
Tests for newrelic custom metrics.
"""
from django.test import TestCase
from mock import patch, call

import newrelic_custom_metrics


class TestNewRelicCustomMetrics(TestCase):
    """
    Test the newrelic_custom_metrics middleware and helpers
    """

    @patch('newrelic.agent')
    def test_cache_normal_contents(self, mock_newrelic_agent):
        """
        Test normal usage of collecting and reporting custom New Relic metrics
        """
        newrelic_custom_metrics.accumulate('hello', 10)
        newrelic_custom_metrics.accumulate('world', 10)
        newrelic_custom_metrics.accumulate('world', 10)
        newrelic_custom_metrics.increment('foo')
        newrelic_custom_metrics.increment('foo')

        # based on the metric data above, we expect the following calls to newrelic:
        nr_agent_calls_expected = [
            call('hello', 10),
            call('world', 20),
            call('foo', 2),
        ]

        # fake a response to trigger metrics reporting
        newrelic_custom_metrics.middleware.NewRelicCustomMetrics().process_response(
            'fake request',
            'fake response',
        )

        # Assert call counts to newrelic.agent.add_custom_parameter()
        expected_call_count = len(nr_agent_calls_expected)
        measured_call_count = mock_newrelic_agent.add_custom_parameter.call_count
        self.assertEqual(expected_call_count, measured_call_count)

        # Assert call args to newrelic.agent.add_custom_parameter().  Due to
        # the nature of python dicts, call order is undefined.
        mock_newrelic_agent.add_custom_parameter.has_calls(nr_agent_calls_expected, any_order=True)
