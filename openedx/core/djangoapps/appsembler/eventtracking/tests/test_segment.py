"""
Test the appsembler.eventtracking.segment module
"""

from mock import patch, Mock
from django.test import TestCase
import ddt

from openedx.core.djangoapps.appsembler.eventtracking.segment import (
    SegmentTopLevelPropertiesProcessor
)

from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteConfigurationFactory
)

EVENTTRACKING_MODULE = 'openedx.core.djangoapps.appsembler.eventtracking'


@ddt.ddt
class SegmentTests(TestCase):
    """
    Very basic and very much not exhaustive testing of
    appsembler.eventtracking.segment module
    """
    def setUp(self):
        self.site_config = SiteConfigurationFactory()

    def test_call_without_modify(self):
        """
        A bit about the event dict.
        It can have the following keys: 'org', 'course_id' but doesn't have to
        have them
        """

        mock_site_config = Mock()
        mock_site_config.get_value.return_value = True
        event = dict(data=dict(alpha='apples', bravo='bananas'))

        with patch(EVENTTRACKING_MODULE + '.segment.get_site_config_for_event',
                   return_value=mock_site_config):
            obj = SegmentTopLevelPropertiesProcessor()
            obj(event)

        assert set(['alpha', 'bravo']) <= set(event.keys())

    # @patch('django.conf.settings.COPY_SEGMENT_EVENT_PROPERTIES_TO_TOP_LEVEL', True)
    def test_call_with_modify(self):
        """
        A bit about the event dict.
        It can have the following keys: 'org', 'course_id' but doesn't have to
        have them
        """
        mock_site_config = Mock()
        mock_site_config.get_value.return_value = False
        event = dict(data=dict(alpha='apples', bravo='bananas'))
        with patch(EVENTTRACKING_MODULE + '.segment.get_site_config_for_event',
                   return_value=mock_site_config):
            obj = SegmentTopLevelPropertiesProcessor()
            obj(event)
            assert not set(['alpha', 'bravo']) <= set(event.keys())
