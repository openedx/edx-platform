""" Tests the contents of the __init__.py file """


from django.test import TestCase

from openedx.features.calendar_sync import get_calendar_event_id
from student.tests.factories import UserFactory

TEST_PASSWORD = 'test'


class TestCalendarSyncInit(TestCase):
    """ Tests for the contents of __init__.py """
    def setUp(self):
        super(TestCalendarSyncInit, self).setUp()
        self.user = UserFactory(password=TEST_PASSWORD)

    def test_get_calendar_event_id(self):
        block_key = 'block-v1:Org+Number+Term+type@sequential+block@gibberish'
        date_type = 'due'
        event_id = get_calendar_event_id(self.user, block_key, date_type)
        expected = '{username}.{block_key}.{date_type}'.format(
            username=self.user.username, block_key=block_key, date_type=date_type
        )
        self.assertEqual(event_id, expected)
