"""
Test the appsembler.eventtracking.segment module
"""

from mock import patch, Mock
from django.test import TestCase
import ddt

from openedx.core.djangoapps.appsembler.eventtracking.segment import (
    SegmentTopLevelPropertiesProcessor, fix_user_id
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

    def test_fix_user_id_no_context(self):
        """
        Verify that fix_user_id will do nothing if the event is missing <context> key
        """
        event = {
            'user_id': 123,
            'any_other_key': 'abc'
        }
        fix_user_id(event=event)
        assert event == {
            'user_id': 123,
            'any_other_key': 'abc'
        }

    def test_fix_user_id_already_exists(self):
        """
        Verify that fix_user_id will do nothing if [context] key already contains a [user_id]
        """
        event = {
            'context': {
                # if exists, it will be identical to root level, but just pretend another value for the sake of testing
                'user_id': 456,
            },
            'user_id': 123,
            'any_other_key': 'abc'
        }
        fix_user_id(event=event)
        assert event == {
            'context': {
                'user_id': 456,
            },
            'user_id': 123,
            'any_other_key': 'abc'
        }

    def test_fix_user_id_missing(self):
        """
        Verify that fix_user_id will fill <context> with the missing <user_id> by copying it from root level
        """
        event = {
            'context': {
            },
            'user_id': 123,
            'any_other_key': 'abc'
        }
        fix_user_id(event=event)
        assert event == {
            'context': {
                'user_id': 123,
            },
            'user_id': 123,
            'any_other_key': 'abc'
        }

    def test_fix_user_id_both_missing(self):
        """
        Verify that fix_user_id will fill <context> with <user_id> value equal to None if <user_id> is missing from
        root level too. This case should never happen; but still a safe way to avoid crashes for any reason
        """
        event = {
            'context': {
            },
            # 'user_id' is missing for unknown reason!
            'any_other_key': 'abc'
        }
        fix_user_id(event=event)
        assert event == {
            'context': {
                'user_id': None,
            },
            'any_other_key': 'abc'
        }

    def test_fix_user_id_in_processor(self):
        """
        Verify that Segment processor is having <user_id> fixed in <context>
        """
        event = {
            'context': {},
            'data': {},
            'user_id': 123,
        }
        mock_site_config = Mock()
        mock_site_config.get_value.return_value = True
        with patch(EVENTTRACKING_MODULE + '.segment.get_site_config_for_event', return_value=mock_site_config):
            processor = SegmentTopLevelPropertiesProcessor()
            processor(event)

        assert event == {
            'context': {'user_id': 123},
            'data': {},
            'user_id': 123,
        }
