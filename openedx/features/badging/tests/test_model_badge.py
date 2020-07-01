from django.contrib.auth.models import User
from django.test import TestCase

from nodebb.constants import CONVERSATIONALIST_ENTRY_INDEX
from openedx.features.badging.constants import CONVERSATIONALIST
from openedx.features.badging.models import Badge
from openedx.features.badging.tests.factories import BadgeFactory


class BadgeModelTestCases(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser',
                                             password='12345')

    def test_save_badge_normal(self):
        """
        Trying to save a Badge object with all the right arguments.
        """
        badge = Badge(name="Sample Badge",
                      threshold=30,
                      type=CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX],
                      image="path/to/image",
                      date_created=None)
        self.assertEqual(badge.save(), None)

    def test_get_badges_json(self):
        """
        Check if get_badges_json returns empty json if no badge exists of provided badge_type
        """
        expected_result = '[]'
        returned_result = Badge.objects.get_badges_json(badge_type="no_match_")
        self.assertEqual(expected_result, returned_result)

    def test_get_badges_json_is_ordered(self):
        """
        Check get_badges_json returns badges in correct order by threshold
        """
        BadgeFactory(threshold=20)
        BadgeFactory(threshold=10)

        result = Badge.objects.get_badges_json(badge_type=CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX])
        threshold_index_1 = result.index('"threshold":10')
        threshold_index_2 = result.index('"threshold":20')
        self.assertGreater(threshold_index_2, threshold_index_1)

