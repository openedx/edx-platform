from ddt import data, ddt, unpack
from django.db import DataError, IntegrityError
from django.test import TestCase

from openedx.features.smart_referral.models import SmartReferral

from .factories import SmartReferralFactory


@ddt
class SmartReferralModelTest(TestCase):
    """
    Test cases for SmartReferral model
    """

    def test_save_smart_referral_model_with_mandatory_fields_successfully(self):
        """
        Create a referral, and assert that it is saved successfully with all mandatory data
        """
        referral = SmartReferralFactory()

        referral_from_database = SmartReferral.objects.get(pk=referral.id)

        self.assertIsNotNone(referral_from_database)
        self.assertEqual(referral.contact_email, referral.contact_email)
        # test default value of is_contact_reg_completed
        self.assertFalse(referral_from_database.is_contact_reg_completed)

    @data('user', 'contact_email', 'is_contact_reg_completed')
    def test_required_fields(self, field_name):
        """
        Create referral for each required field and assert that referral fails to save if that field is not
        provided
        """
        with self.assertRaises(IntegrityError):
            SmartReferralFactory(**{field_name: None})
