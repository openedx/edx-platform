"""
Tests for all the models in the registration_extension app
"""
import datetime

import pytest

from .factories import ExtendedUserProfileFactory


@pytest.mark.parametrize('is_saudi_national, has_birthdate, expected_output', [
    (True, True, True), (True, False, False), (False, True, False), (False, False, False)
])
@pytest.mark.django_db
def test_is_saudi_national_and_has_birthdate_property(is_saudi_national, has_birthdate, expected_output):
    """
    Test that `is_saudi_national_and_has_birthdate` property of the ExtendedUserProfile model returns
    False unless the extended profile has `saudi_national` as true and birthdate field is added
    """
    extended_profile = ExtendedUserProfileFactory()
    extended_profile.saudi_national = is_saudi_national

    if has_birthdate:
        extended_profile.birth_date = datetime.date(1990, 1, 1)

    assert extended_profile.is_saudi_national_and_has_birthdate == expected_output
