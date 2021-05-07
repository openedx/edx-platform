""" Tests for LMS helper """
from datetime import datetime

import pytest

from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory
from openedx.adg.lms.helpers import convert_date_time_zone_and_format, get_user_first_name
from openedx.adg.lms.webinars.constants import WEBINAR_DATE_TIME_FORMAT, WEBINAR_DEFAULT_TIME_ZONE
from openedx.adg.lms.webinars.tests.factories import WebinarFactory

from .constants import FIRST_NAME, FIRST_PART_OF_FULL_NAME


@pytest.mark.django_db
@pytest.mark.parametrize(
    'first_name, full_name, expected_first_name', [
        (FIRST_NAME, '', FIRST_NAME),
        ('', f'{FIRST_PART_OF_FULL_NAME} last_part_of_full_name', FIRST_PART_OF_FULL_NAME)
    ],
    ids=['user_with_first_name', 'user_with_full_name']
)
def test_get_user_first_name(first_name, full_name, expected_first_name):
    """
    Tests `get_user_first_name` helper
    """
    user = UserFactory(first_name=first_name)
    UserProfileFactory(user=user, name=full_name)

    assert get_user_first_name(user) == expected_first_name


@pytest.mark.django_db
def test_convert_date_time_zone_and_format():
    """
    Test convert_time_zone helper
    """
    webinar = WebinarFactory(start_time=datetime(2020, 1, 1, 13, 10, 1))

    expected_date_time = 'Wednesday, January 01, 2020 04:10 PM AST'
    actual_date_time = convert_date_time_zone_and_format(
        webinar.start_time, WEBINAR_DEFAULT_TIME_ZONE, WEBINAR_DATE_TIME_FORMAT
    )

    assert expected_date_time == actual_date_time
