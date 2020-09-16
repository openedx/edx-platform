"""
All helpers for custom settings app
"""
from datetime import datetime

import pytz

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

DATE_FORMAT = "%m/%d/%Y"


def get_course_open_date_from_settings(settings):
    """
    Get course open date from settings, if exists, in MM/DD/YYY format else return empty string

    Args:
        settings (CustomSettings): Custom settings model object

    Returns:
        string: Date in MM/DD/YYYY format or empty string
    """
    return '' if not settings.course_open_date else settings.course_open_date.strftime(DATE_FORMAT)


def validate_course_open_date(settings, course_open_date):
    """
    This method compares course start date and course open date and make sure that course open date is greater
    than start date

    Args:
        settings (CustomSettings): Custom settings model object
        course_open_date (Date): Course open date

    Returns:
        Date: Validated course open date or None
    """
    if course_open_date:
        if isinstance(datetime.strptime(course_open_date, DATE_FORMAT), datetime):
            course_open_date = datetime.strptime(course_open_date, DATE_FORMAT)
            utc = pytz.UTC
            course_open_date = course_open_date.replace(tzinfo=utc)
            course = CourseOverview.objects.get(id=settings.id)

            if course.end < course_open_date or course_open_date < course.start:
                raise ValueError('invalid date object', course_open_date)

        else:
            raise ValueError('invalid date object', course_open_date)
    else:
        course_open_date = None
    return course_open_date
