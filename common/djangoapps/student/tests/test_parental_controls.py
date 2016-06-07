"""Unit tests for parental controls."""

import datetime
from django.test import TestCase
from django.test.utils import override_settings

from student.models import UserProfile
from student.tests.factories import UserFactory


class ProfileParentalControlsTest(TestCase):
    """Unit tests for requires_parental_consent."""

    password = "test"

    def setUp(self):
        super(ProfileParentalControlsTest, self).setUp()
        self.user = UserFactory.create(password=self.password)
        self.profile = UserProfile.objects.get(id=self.user.id)

    def set_year_of_birth(self, year_of_birth):
        """
        Helper method that creates a mock profile for the specified user.
        """
        self.profile.year_of_birth = year_of_birth
        self.profile.save()

    def test_no_year_of_birth(self):
        """Verify the behavior for users with no specified year of birth."""
        self.assertTrue(self.profile.requires_parental_consent())
        self.assertTrue(self.profile.requires_parental_consent(default_requires_consent=True))
        self.assertFalse(self.profile.requires_parental_consent(default_requires_consent=False))

    @override_settings(PARENTAL_CONSENT_AGE_LIMIT=None)
    def test_no_parental_controls(self):
        """Verify the behavior for all users when parental controls are not enabled."""
        self.assertFalse(self.profile.requires_parental_consent())
        self.assertFalse(self.profile.requires_parental_consent(default_requires_consent=True))
        self.assertFalse(self.profile.requires_parental_consent(default_requires_consent=False))

        # Verify that even a child does not require parental consent
        current_year = datetime.datetime.now().year
        self.set_year_of_birth(current_year - 10)
        self.assertFalse(self.profile.requires_parental_consent())

    def test_adult_user(self):
        """Verify the behavior for an adult."""
        current_year = datetime.datetime.now().year
        self.set_year_of_birth(current_year - 20)
        self.assertFalse(self.profile.requires_parental_consent())
        self.assertTrue(self.profile.requires_parental_consent(age_limit=21))

    def test_child_user(self):
        """Verify the behavior for a child."""
        current_year = datetime.datetime.now().year

        # Verify for a child born 13 years agp
        self.set_year_of_birth(current_year - 13)
        self.assertTrue(self.profile.requires_parental_consent())
        self.assertTrue(self.profile.requires_parental_consent(date=datetime.date(current_year, 12, 31)))
        self.assertFalse(self.profile.requires_parental_consent(date=datetime.date(current_year + 1, 1, 1)))

        # Verify for a child born 14 years ago
        self.set_year_of_birth(current_year - 14)
        self.assertFalse(self.profile.requires_parental_consent())
        self.assertFalse(self.profile.requires_parental_consent(date=datetime.date(current_year, 1, 1)))

    def test_profile_image(self):
        """Verify that a profile's image obeys parental controls."""

        # Verify that an image cannot be set for a user with no year of birth set
        self.profile.profile_image_uploaded_at = datetime.datetime.now()
        self.profile.save()
        self.assertFalse(self.profile.has_profile_image)

        # Verify that an image can be set for an adult user
        current_year = datetime.datetime.now().year
        self.set_year_of_birth(current_year - 20)
        self.profile.profile_image_uploaded_at = datetime.datetime.now()
        self.profile.save()
        self.assertTrue(self.profile.has_profile_image)

        # verify that a user's profile image is removed when they switch to requiring parental controls
        self.set_year_of_birth(current_year - 10)
        self.profile.save()
        self.assertFalse(self.profile.has_profile_image)
