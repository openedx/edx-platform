from datetime import datetime

import pytz

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

DATE_FORMAT = "%m/%d/%Y"


def get_course_open_date_from_settings(settings):
    """
    :param settings:
    :return course open date:
    """
    return "" if not settings.course_open_date else settings.course_open_date.strftime(DATE_FORMAT)


def validate_course_open_date(settings, course_open_date):

    """
    this method compares course start date and course open date
    and make sure that course open date is greater than start date
    :param settings:
    :param course_open_date:
    :return:
        validated course open date or none
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
