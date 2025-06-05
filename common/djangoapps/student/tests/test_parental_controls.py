"""Unit tests for parental controls."""


from django.test import TestCase
from django.test.utils import override_settings
from django.utils.timezone import now

from common.djangoapps.student.models import UserProfile
from common.djangoapps.student.tests.factories import UserFactory


class ProfileParentalControlsTest(TestCase):
    """Unit tests for requires_parental_consent."""

    password = "test"

    def setUp(self):
        super().setUp()
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
        assert self.profile.requires_parental_consent()
        assert self.profile.requires_parental_consent(default_requires_consent=True)
        assert not self.profile.requires_parental_consent(default_requires_consent=False)

    @override_settings(PARENTAL_CONSENT_AGE_LIMIT=None)
    def test_no_parental_controls(self):
        """Verify the behavior for all users when parental controls are not enabled."""
        assert not self.profile.requires_parental_consent()
        assert not self.profile.requires_parental_consent(default_requires_consent=True)
        assert not self.profile.requires_parental_consent(default_requires_consent=False)

        # Verify that even a child does not require parental consent
        current_year = now().year
        self.set_year_of_birth(current_year - 10)
        assert not self.profile.requires_parental_consent()

    def test_adult_user(self):
        """Verify the behavior for an adult."""
        current_year = now().year
        self.set_year_of_birth(current_year - 20)
        assert not self.profile.requires_parental_consent()
        assert self.profile.requires_parental_consent(age_limit=21)

    def test_child_user(self):
        """Verify the behavior for a child."""
        current_year = now().year

        # Verify for a child born 13 years agp
        self.set_year_of_birth(current_year - 13)
        assert self.profile.requires_parental_consent()
        assert self.profile.requires_parental_consent(year=current_year)
        assert not self.profile.requires_parental_consent(year=current_year + 1)

        # Verify for a child born 14 years ago
        self.set_year_of_birth(current_year - 14)
        assert not self.profile.requires_parental_consent()
        assert not self.profile.requires_parental_consent(year=current_year)
