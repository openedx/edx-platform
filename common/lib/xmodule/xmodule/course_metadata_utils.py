"""
Simple utility functions that operate on course metadata.

This is a place to put simple functions that operate on course metadata. It
allows us to share code between the CourseDescriptor and CourseOverview
classes, which both need these type of functions.
"""
from base64 import b32encode
from datetime import datetime, timedelta
import dateutil.parser
from math import exp

from openedx.core.lib.time_zone_utils import get_time_zone_abbr
from pytz import utc

from .fields import Date

DEFAULT_START_DATE = datetime(2030, 1, 1, tzinfo=utc)


def clean_course_key(course_key, padding_char):
    """
    Encode a course's key into a unique, deterministic base32-encoded ID for
    the course.

    Arguments:
        course_key (CourseKey): A course key.
        padding_char (str): Character used for padding at end of the encoded
            string. The standard value for this is '='.
    """
    return "course_{}".format(
        b32encode(unicode(course_key)).replace('=', padding_char)
    )


def number_for_course_location(location):
    """
    Given a course's block usage locator, returns the course's number.

    This is a "number" in the sense of the "course numbers" that you see at
    lots of universities. For example, given a course
    "Intro to Computer Science" with the course key "edX/CS-101/2014", the
    course number would be "CS-101"

    Arguments:
        location (BlockUsageLocator): The usage locator of the course in
            question.
    """
    return location.course


def has_course_started(start_date):
    """
    Given a course's start datetime, returns whether the current time's past it.

    Arguments:
        start_date (datetime): The start datetime of the course in question.
    """
    # TODO: This will throw if start_date is None... consider changing this behavior?
    return datetime.now(utc) > start_date


def has_course_ended(end_date):
    """
    Given a course's end datetime, returns whether
        (a) it is not None, and
        (b) the current time is past it.

    Arguments:
        end_date (datetime): The end datetime of the course in question.
    """
    return datetime.now(utc) > end_date if end_date is not None else False


def course_starts_within(start_date, look_ahead_days):
    """
    Given a course's start datetime and look ahead days, returns True if
    course's start date falls within look ahead days otherwise False

    Arguments:
        start_date (datetime): The start datetime of the course in question.
        look_ahead_days (int): number of days to see in future for course start date.
    """
    return datetime.now(utc) + timedelta(days=look_ahead_days) > start_date


def course_start_date_is_default(start, advertised_start):
    """
    Returns whether a course's start date hasn't yet been set.

    Arguments:
        start (datetime): The start datetime of the course in question.
        advertised_start (str): The advertised start date of the course
            in question.
    """
    return advertised_start is None and start == DEFAULT_START_DATE


def _datetime_to_string(date_time, format_string, time_zone, strftime_localized):
    """
    Formats the given datetime with the given function and format string.

    Adds time zone abbreviation to the resulting string if the format is DATE_TIME or TIME.

    Arguments:
        date_time (datetime): the datetime to be formatted
        format_string (str): the date format type, as passed to strftime
        time_zone (pytz time zone): the time zone to convert to
        strftime_localized ((datetime, str) -> str): a nm localized string
            formatting function
    """
    result = strftime_localized(date_time.astimezone(time_zone), format_string)
    abbr = get_time_zone_abbr(time_zone, date_time)
    return (
        result + ' ' + abbr if format_string in ['DATE_TIME', 'TIME', 'DAY_AND_TIME']
        else result
    )


def course_start_datetime_text(start_date, advertised_start, format_string, time_zone, ugettext, strftime_localized):
    """
    Calculates text to be shown to user regarding a course's start
    datetime in specified time zone.

    Prefers .advertised_start, then falls back to .start.

    Arguments:
        start_date (datetime): the course's start datetime
        advertised_start (str): the course's advertised start date
        format_string (str): the date format type, as passed to strftime
        time_zone (pytz time zone): the time zone to convert to
        ugettext ((str) -> str): a text localization function
        strftime_localized ((datetime, str) -> str): a localized string
            formatting function
    """
    if advertised_start is not None:
        # TODO: This will return an empty string if advertised_start == ""... consider changing this behavior?
        try:
            # from_json either returns a Date, returns None, or raises a ValueError
            parsed_advertised_start = Date().from_json(advertised_start)
            if parsed_advertised_start is not None:
                # In the Django implementation of strftime_localized, if
                # the year is <1900, _datetime_to_string will raise a ValueError.
                return _datetime_to_string(parsed_advertised_start, format_string, time_zone, strftime_localized)
        except ValueError:
            pass
        return advertised_start.title()
    elif start_date != DEFAULT_START_DATE:
        return _datetime_to_string(start_date, format_string, time_zone, strftime_localized)
    else:
        _ = ugettext
        # Translators: TBD stands for 'To Be Determined' and is used when a course
        # does not yet have an announced start date.
        return _('TBD')


def course_end_datetime_text(end_date, format_string, time_zone, strftime_localized):
    """
    Returns a formatted string for a course's end date or datetime.

    If end_date is None, an empty string will be returned.

    Arguments:
        end_date (datetime): the end datetime of a course
        format_string (str): the date format type, as passed to strftime
        time_zone (pytz time zone): the time zone to convert to
        strftime_localized ((datetime, str) -> str): a localized string
            formatting function
    """
    return (
        _datetime_to_string(end_date, format_string, time_zone, strftime_localized) if end_date is not None
        else ''
    )


def may_certify_for_course(certificates_display_behavior, certificates_show_before_end, has_ended):
    """
    Returns whether it is acceptable to show the student a certificate download
    link for a course.

    Arguments:
        certificates_display_behavior (str): string describing the course's
            certificate display behavior.
            See CourseFields.certificates_display_behavior.help for more detail.
        certificates_show_before_end (bool): whether user can download the
            course's certificates before the course has ended.
        has_ended (bool): Whether the course has ended.
    """
    show_early = (
        certificates_display_behavior in ('early_with_info', 'early_no_info')
        or certificates_show_before_end
    )
    return show_early or has_ended


def sorting_score(start, advertised_start, announcement):
    """
    Returns a tuple that can be used to sort the courses according
    to how "new" they are. The "newness" score is computed using a
    heuristic that takes into account the announcement and
    (advertised) start dates of the course if available.

    The lower the number the "newer" the course.
    """
    # Make courses that have an announcement date have a lower
    # score than courses than don't, older courses should have a
    # higher score.
    announcement, start, now = sorting_dates(start, advertised_start, announcement)
    scale = 300.0  # about a year
    if announcement:
        days = (now - announcement).days
        score = -exp(-days / scale)
    else:
        days = (now - start).days
        score = exp(days / scale)
    return score


def sorting_dates(start, advertised_start, announcement):
    """
    Utility function to get datetime objects for dates used to
    compute the is_new flag and the sorting_score.
    """
    try:
        start = dateutil.parser.parse(advertised_start)
        if start.tzinfo is None:
            start = start.replace(tzinfo=utc)
    except (ValueError, AttributeError):
        start = start

    now = datetime.now(utc)

    return announcement, start, now
