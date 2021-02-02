"""
All tests for marketplace models
"""
from ddt import data, unpack, ddt
from django.db import IntegrityError, DataError
from django.test import TestCase

from openedx.features.idea.constants import CITY_MAX_LENGTH
from openedx.features.marketplace.models import MarketplaceRequest
from openedx.features.marketplace.tests.factories import ChallengeFactory


@ddt
class ChallengeModelTest(TestCase):
    """Test cases for challenge model"""

    def test_save_challenge_model_with_mandatory_fields_successfully(self):
        """Create an challenge, and assert that it is saved successfully with all mandatory data"""
        challenge = ChallengeFactory()

        challenge_from_database = MarketplaceRequest.objects.get(pk=challenge.id)

        self.assertEquals(challenge_from_database.user_services, ['healthcare-supplies', 'other value'])

        self.assertIsNotNone(challenge_from_database)

    def test_location_from_city_and_country(self):
        """Create an challenge and assert that location property is accessible in specific format"""
        challenge = ChallengeFactory(country='PK', city='Lahore')
        self.assertIsNotNone(challenge.location, 'Lahore, Pakistan')

    @data('user', 'description')
    def test_required_fields(self, field_name):
        """
        Create challenge for each required field and assert that challenge fails to save if that field is not
        provided
        """
        with self.assertRaises(IntegrityError):
            ChallengeFactory(**{field_name: None})

    @data(['city', CITY_MAX_LENGTH])
    @unpack
    def test_max_length(self, field_name, max_length):
        """
        Create challenge for each field which has max length limit and
        assert that challenge fail to save if max length limit exceeds
        """
        with self.assertRaises(DataError):
            string_exceeding_max_limit = 'n' * (max_length + 1)
            ChallengeFactory(**{field_name: string_exceeding_max_limit})

    def test_visual_attachments(self):
        """Create challenge with visual attachments and verify that it saves successfully"""
        challenge = ChallengeFactory(
            image='my_image.jpg',
            file='my_file.docx',
            video_link='https://example.com'
        )

        challenge_from_databased = MarketplaceRequest.objects.get(pk=challenge.id)

        self.assertIsNotNone(challenge_from_databased)
        self.assertIsNotNone(challenge.image)
        self.assertIsNotNone(challenge.file)
        self.assertEqual(challenge.image.name, challenge_from_databased.image.name)
        self.assertEqual(challenge.file.name, challenge_from_databased.file.name)
        self.assertEqual(challenge.video_link, challenge_from_databased.video_link)
