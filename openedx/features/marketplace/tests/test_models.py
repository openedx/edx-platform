from ddt import data, ddt, unpack
from django.db import DataError, IntegrityError
from django.test import TestCase

from openedx.features.marketplace.models import MarketplaceRequest

from .factories import ChallengeFactory


@ddt
class ChallengeModelTest(TestCase):
    """Test cases for MarketPlaceRequest model"""

    def test_save_challenge_model_with_mandatory_fields_successfully(self):
        """Create a challenge, and assert that it is saved successfully with all mandatory data"""
        challenge = ChallengeFactory()

        challenge_from_database = MarketplaceRequest.objects.get(pk=challenge.id)

        self.assertIsNotNone(challenge_from_database)
        self.assertEqual(challenge.description, challenge_from_database.description)

    @data('user', 'description')
    def test_required_fields(self, field_name):
        """
        Create challenge for each required field and assert that challenge fails to save if that field is not
        provided
        """
        with self.assertRaises(IntegrityError):
            ChallengeFactory(**{field_name: None})
