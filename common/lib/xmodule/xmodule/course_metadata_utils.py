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

from pytz import utc

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
