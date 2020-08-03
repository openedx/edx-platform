from datetime import datetime

import pytest
from mock import Mock
from pytz import UTC

from custom_settings.helpers import get_course_open_date_from_settings, validate_course_open_date
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


@pytest.mark.parametrize(
    'course_open_date, expected',
    [('', ''), (None, ''), (datetime(2020, 12, 17), '12/17/2020')],
    ids=['course_open_date_empty', 'course_open_date_None', 'course_open_date_valid']
)
def test_get_course_open_date_from_settings(course_open_date, expected):
    """Assert that course_open_date is in proper date format"""
    settings = Mock(spec=['settings'], course_open_date=course_open_date)
    assert get_course_open_date_from_settings(settings) == expected


@pytest.mark.django_db
@pytest.fixture()
def course_open_date_settings_fixture():
    """A fixture to create CourseOverview test data and return mocked settings object with CourseOverview id"""
    course_start_date = datetime(2020, 1, 1, tzinfo=UTC)
    course_end_date = datetime(2021, 1, 1, tzinfo=UTC)
    course_overview = CourseOverviewFactory(start=course_start_date, end=course_end_date)
    return Mock(spec=['settings'], id=course_overview.id)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'course_open_date, expectation',
    [
        pytest.param('2020/12/17', pytest.raises(ValueError), id='course_open_date_invalid_format'),
        pytest.param('1/1/2019', pytest.raises(ValueError), id='course_open_date_lt_start_date'),
        pytest.param('1/1/2022', pytest.raises(ValueError), id='course_open_date_gt_end_date'),
    ]
)
def test_validate_course_open_date_exceptions(course_open_date_settings_fixture, course_open_date, expectation):
    """Test all cases where function can raise exceptions"""
    with expectation:
        validate_course_open_date(course_open_date_settings_fixture, course_open_date)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'course_open_date, expected',
    [
        pytest.param('', None, id='course_open_date_empty'),
        pytest.param('1/1/2020', datetime(2020, 1, 1, tzinfo=UTC), id='successfully'),
    ]
)
def test_validate_course_open_date(course_open_date_settings_fixture, course_open_date, expected):
    """Test cases for success case and when course_open_date is empty"""
    assert validate_course_open_date(course_open_date_settings_fixture, course_open_date) == expected
