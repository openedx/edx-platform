"""
Tests that BadgeCollection behaves correctly when initializing and when creating lists of badges, and test that
other smaller classes that BadgeCollection uses also behave properly.
"""

from mock import patch

from django.test import TestCase

import courseware.badges as badges


@patch('courseware.badges._fetch')
class FailedFetchTestCase(TestCase):
    """
    Test that badges.BadgeCollection.__init__ behaves correctly when _fetch throws BadgingServiceError.
    BadgeCollection.__init__ should re-raise the BadgingServiceError.
    """

    @staticmethod
    def temp_fetch(url):  # unused arguments  # pylint: disable=W0613
        """
        Raise BadgingServiceError, imitating a _fetch method that always fails.
        """
        raise badges.BadgingServiceError()

    def test_with_course(self, mock_fetch):
        """
        Case in which BadgeCollection receives a course id.
        """
        mock_fetch.side_effect = self.temp_fetch

        with self.assertRaises(badges.BadgingServiceError):
            badges.BadgeCollection("", "")

    def test_without_course(self, mock_fetch):
        """
        Case in which BadgeCollection does not receive a course id.
        """
        mock_fetch.side_effect = self.temp_fetch

        with self.assertRaises(badges.BadgingServiceError):
            badges.BadgeCollection("")


@patch('courseware.badges._fetch')
class BlankBadgeDataTestCase(TestCase):
    """
    Test that badges.BadgeCollection.__init__ behaves correctly on empty inputs.
    """

    @staticmethod
    def temp_fetch(url):
        """
        Returns blank fake data depending on the URL passed in.
        """
        if 's/.json' in url:  # list endpoint
            return []
        else:
            return {}

    def test_blank_data_with_course(self, mock_fetch):
        """
        Case when BadgeCollection receives a course id.
        """
        mock_fetch.side_effect = self.temp_fetch

        output = badges.BadgeCollection('', '')
        self.assertEquals(output.get_badges(), [])
        self.assertEquals(output.get_earned_badges(), [])
        self.assertEquals(output.get_unlockable_badges(), [])
        self.assertEquals(output.get_badge_urls(), '[]')

    def test_blank_data_without_course(self, mock_fetch):
        """
        Case when BadgeCollection does not receive a course id.
        """
        mock_fetch.side_effect = self.temp_fetch

        output = badges.BadgeCollection('')
        self.assertEquals(output.get_badges(), [])
        self.assertEquals(output.get_earned_badges(), [])
        self.assertEquals(output.get_unlockable_badges(), [])
        self.assertEquals(output.get_badge_urls(), '[]')


@patch('courseware.badges.BadgeCollection.__init__')
class BadgeCollectionListsTestCase(TestCase):
    """
    Check that BadgeCollection correctly filters and returns lists of Badges when the methods get_badges,
    get_badge_urls, get_unlockable_badges, and get_earned_badges are called.
    """

    def setUp(self):
        """
        Create a BadgeCollection and save it for testing.
        """
        issuer = badges.Issuer({
            'edx_href': '/issuers/1/.json',
            'name': 'Fake Issuer',
            'url': 'http://www.edx.org/',
            'edx_course': 'MITx/19.001x/Fake_Course'
        })
        badgeclass = badges.Badgeclass({
            'edx_href': '/badgeclasses/1/.json',
            'issuer': '/issuers/1/.json',
            'name': 'Fake Badgeclass',
            'description': 'fake description',
            'criteria': 'http://www.edx.org/',
            'image': '/somewhere/default.png',
            'edx_number_awarded': '42',
        })

        self.badge_1 = badges.Badge(badgeclass, issuer)
        self.badge_2 = badges.Badge(badgeclass, issuer)
        self.badge_3 = badges.EarnedBadge({
            'edx_href': '/badges/1/.json',
            'image': '/somewhere/default2.png',
            'issuedOn': '2013-01-01',
        }, badgeclass, issuer)

        self.badges = [self.badge_1, self.badge_2, self.badge_3]

    def test_get_badges(self, mock_init):
        """
        Check that BadgeCollection.get_badges returns all badges.
        """
        mock_init.return_value = None
        badge_collection = badges.BadgeCollection()
        badge_collection.badges = self.badges

        output = badge_collection.get_badges()
        self.assertItemsEqual(self.badges, output)

    def test_get_earned_badges(self, mock_init):
        """
        Check that BadgeCollection.get_earned_badges returns only instances of EarnedBadge.
        """
        mock_init.return_value = None
        badge_collection = badges.BadgeCollection()
        badge_collection.badges = self.badges

        output = badge_collection.get_earned_badges()
        self.assertItemsEqual([self.badge_3], output)

    def test_get_unlockable_badges(self, mock_init):
        """
        Check that BadgeCollection.get_unlockable_badges returns only instances of Badge that aren't EarnedBadge.
        """
        mock_init.return_value = None
        badge_collection = badges.BadgeCollection()
        badge_collection.badges = self.badges

        output = badge_collection.get_unlockable_badges()
        self.assertItemsEqual([self.badge_1, self.badge_2], output)

    def test_get_badge_urls(self, mock_init):
        """
        Check that BadgeCollection.get_badge_urls returns a json-dumped string; the JSON is a list of URLs, with each
        URL pointing to an earned badge.
        """
        mock_init.return_value = None
        badge_collection = badges.BadgeCollection()
        badge_collection.badges = self.badges

        output = badge_collection.get_badge_urls()
        self.assertItemsEqual('[\"/badges/1/.json\"]', output)


class BadgeClassesTestCase(TestCase):
    """
    Test that the classes Badge, EarnedBadge, Badgeclass, and Issuer in badges.py behave correctly.
    """

    issuer_info = {
        'edx_href': '/issuers/1/.json',
        'name': 'Fake Issuer',
        'url': 'http://www.edx.org/',
        'edx_course': 'MITx/19.001x/Fake_Course'
    }
    badgeclass_info = {
        'edx_href': '/badgeclasses/1/.json',
        'issuer': '/issuers/1/.json',
        'name': 'Fake Badgeclass',
        'description': 'fake description',
        'criteria': 'http://www.edx.org/',
        'image': '/somewhere/default.png',
        'edx_number_awarded': '42',
    }
    badge_info = {
        'edx_href': '/badges/1/.json',
        'image': '/somewhere/default2.png',
        'issuedOn': '2013-01-01',
    }

    def test_badgeclass_init(self):
        """
        Test that Badgeclass initializes with all properties correctly.
        """
        badgeclass = badges.Badgeclass(self.badgeclass_info)
        self.verify_badgeclass(badgeclass)

    def test_badgeclass_failure(self):
        """
        Test that a BadgingServiceError is thrown if required data is missing when Badgeclass is constructed.
        """
        for key in self.badgeclass_info.keys():
            new_info = self.badgeclass_info.copy()
            del new_info[key]

            with self.assertRaises(badges.BadgingServiceError):
                badges.Badgeclass(new_info)

    def test_issuer_init(self):
        """
        Test that Issuer initializes with all properties correctly.
        """
        issuer = badges.Issuer(self.issuer_info)
        self.verify_issuer(issuer)

    def test_issuer_failure(self):
        """
        Test that a BadgingServiceError is thrown if required data is missing when Issuer is constructed.
        """
        for key in self.issuer_info.keys():
            new_info = self.issuer_info.copy()
            del new_info[key]

            with self.assertRaises(badges.BadgingServiceError):
                badges.Issuer(new_info)

    def test_badge_init(self):
        """
        Test that Badge initializes with all properties correctly.
        """
        badgeclass = badges.Badgeclass(self.badgeclass_info)
        issuer = badges.Issuer(self.issuer_info)
        badge = badges.Badge(badgeclass, issuer)

        self.assertFalse(badge.is_earned)
        self.verify_badgeclass(badge.badgeclass)
        self.verify_issuer(badge.issuer)

    def test_earned_badge_init(self):
        """
        Test that EarnedBadge initializes with all properties correctly.
        """
        badgeclass = badges.Badgeclass(self.badgeclass_info)
        issuer = badges.Issuer(self.issuer_info)
        badge = badges.EarnedBadge(self.badge_info, badgeclass, issuer)

        self.assertTrue(badge.is_earned)
        self.verify_badgeclass(badge.badgeclass)
        self.verify_issuer(badge.issuer)

        self.assertEquals(badge.href, self.badge_info['edx_href'])
        self.assertEquals(badge.image, self.badge_info['image'])
        self.assertEquals(badge.issued_on, self.badge_info['issuedOn'])

    def test_earned_badge_failure(self):
        """
        Test that a BadgingServiceError is thrown if required data is missing when EarnedBadge is constructed.
        """
        badgeclass = badges.Badgeclass(self.badgeclass_info)
        issuer = badges.Issuer(self.issuer_info)
        for key in self.badge_info.keys():
            new_info = self.badge_info.copy()
            del new_info[key]

            with self.assertRaises(badges.BadgingServiceError):
                badges.EarnedBadge(new_info, badgeclass, issuer)

    def verify_issuer(self, issuer):
        """
        Helper method: assert that required properties of an Issuer are present and match the passed-in fake data.
        """
        self.assertEquals(issuer.href, self.issuer_info['edx_href'])
        self.assertEquals(issuer.name, self.issuer_info['name'])
        self.assertEquals(issuer.url, self.issuer_info['url'])
        self.assertEquals(issuer.course, self.issuer_info['edx_course'])

    def verify_badgeclass(self, badgeclass):
        """
        Helper method: assert that required properties of a Badgeclass are present and match the passed-in fake data.
        """
        self.assertEquals(badgeclass.href, self.badgeclass_info['edx_href'])
        self.assertEquals(badgeclass.issuer, self.badgeclass_info['issuer'])
        self.assertEquals(badgeclass.name, self.badgeclass_info['name'])
        self.assertEquals(badgeclass.description, self.badgeclass_info['description'])
        self.assertEquals(badgeclass.criteria, self.badgeclass_info['criteria'])
        self.assertEquals(badgeclass.image, self.badgeclass_info['image'])
        self.assertEquals(badgeclass.number_awarded, self.badgeclass_info['edx_number_awarded'])
