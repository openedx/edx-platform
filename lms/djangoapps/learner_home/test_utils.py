"""
Various utilities used for testing/test data.
"""
import datetime
from random import choice, getrandbits, randint
from time import time
from uuid import uuid4

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.factories import CourseFactory


def random_bool():
    """Test util for generating a random boolean"""
    return bool(getrandbits(1))


def random_date(allow_null=False):
    """Test util for generating a random date, optionally blank"""

    # If null allowed, return null half the time
    if allow_null and random_bool():
        return None

    d = randint(1, int(time()))
    return datetime.datetime.fromtimestamp(d, tz=datetime.timezone.utc)


def random_url(allow_null=False):
    """Test util for generating a random URL, optionally blank"""

    # If null allowed, return null half the time
    if allow_null and random_bool():
        return None

    random_uuid = uuid4()
    return choice([f"{random_uuid}.example.com", f"example.com/{random_uuid}"])


def random_grade():
    """Return a random grade (0-100) with 2 decimal places of padding"""
    return randint(0, 10000) / 100


def decimal_to_grade_format(decimal):
    """Util for matching serialized grade format, pads a decimal to 2 places"""
    return "{:.2f}".format(decimal)


def datetime_to_django_format(datetime_obj):
    """Util for matching serialized Django datetime format for comparison"""
    if datetime_obj:
        return datetime_obj.strftime("%Y-%m-%dT%H:%M:%SZ")


def create_test_enrollment(user, course_mode=CourseMode.AUDIT):
    """Create a course and enrollment for the test user. Returns a CourseEnrollment"""
    course = CourseFactory(self_paced=True)

    CourseModeFactory(
        course_id=course.id,
        mode_slug=course_mode,
    )

    return CourseEnrollmentFactory(
        course_id=course.id, mode=course_mode, user_id=user.id
    )
