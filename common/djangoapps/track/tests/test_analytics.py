# pylint: disable=unused-argument, invalid-name

"""test AnalyticsService"""

__author__ = 'Arbisoft'

from unittest import TestCase
from mock import patch, Mock
from track.service import AnalyticsService


def mock_tracker_emit(*args, **kwargs):
    """
    Mocked function of emit
    """
    pass

mock_emit = Mock(side_effect=mock_tracker_emit)


class MockAnalyticsService(TestCase):
    """
    Simple mock of the Analytics Service
    """

    def setUp(self):
        """
        Initializer
        """

        super(MockAnalyticsService, self).setUp()
        self.name = 'service_name'
        self.context = {'url': 'temp.urls.view'}
        self.data = {'id': '1'}

    @patch('eventtracking.tracker.emit', mock_emit)
    def test_analytics_service(self):
        """
        Mocking the emit function
        """
        analytics_service = AnalyticsService()
        analytics_service.emit_event(self.name, self.context, self.data)
        self.assertTrue(mock_emit.called)
