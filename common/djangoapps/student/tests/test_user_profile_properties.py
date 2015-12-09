"""Unit tests for custom UserProfile properties."""

import datetime
import ddt
from django.test import TestCase

from student.models import UserProfile
from student.tests.factories import UserFactory
from django.core.cache import cache


@ddt.ddt
class UserProfilePropertiesTest(TestCase):
    """Unit tests for age, gender_display, and level_of_education_display properties ."""

    password = "test"

    def setUp(self):
        super(UserProfilePropertiesTest, self).setUp()
        self.user = UserFactory.create(password=self.password)
        self.profile = self.user.profile

    def _set_year_of_birth(self, year_of_birth):
        """
        Helper method that sets a birth year for the specified user.
        """
        self.profile.year_of_birth = year_of_birth
        self.profile.save()

    def _set_level_of_education(self, level_of_education):
        """
        Helper method that sets a level of education for the specified user.
        """
        self.profile.level_of_education = level_of_education
        self.profile.save()

    def _set_gender(self, gender):
        """
        Helper method that sets a gender for the specified user.
        """
        self.profile.gender = gender
        self.profile.save()

    @ddt.data(0, 1, 13, 20, 100)
    def test_age(self, age):
        """Verify the age calculated correctly."""
        current_year = datetime.datetime.now().year
        self._set_year_of_birth(current_year - age)

        self.assertEqual(self.profile.age, age)

    def test_age_no_birth_year(self):
        """Verify nothing is returned."""
        self.assertIsNone(self.profile.age)

    @ddt.data(*UserProfile.LEVEL_OF_EDUCATION_CHOICES)
    @ddt.unpack
    def test_display_level_of_education(self, level_enum, display_level):
        """Verify the level of education is displayed correctly."""
        self._set_level_of_education(level_enum)

        self.assertEqual(self.profile.level_of_education_display, display_level)

    def test_display_level_of_education_none_set(self):
        """Verify nothing is returned."""
        self.assertIsNone(self.profile.level_of_education_display)

    @ddt.data(*UserProfile.GENDER_CHOICES)
    @ddt.unpack
    def test_display_gender(self, gender_enum, display_gender):
        """Verify the gender displayed correctly."""
        self._set_gender(gender_enum)

        self.assertEqual(self.profile.gender_display, display_gender)

    def test_display_gender_none_set(self):
        """Verify nothing is returned."""
        self._set_gender(None)

        self.assertIsNone(self.profile.gender_display)

    def test_invalidate_cache_user_profile_country_updated(self):

        country = 'us'
        self.profile.country = country
        self.profile.save()

        cache_key = UserProfile.country_cache_key_name(self.user.id)
        self.assertIsNone(cache.get(cache_key))

        cache.set(cache_key, self.profile.country)
        self.assertEqual(cache.get(cache_key), country)

        country = 'bd'
        self.profile.country = country
        self.profile.save()

        self.assertNotEqual(cache.get(cache_key), country)
        self.assertIsNone(cache.get(cache_key))
