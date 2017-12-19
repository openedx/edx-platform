"""
Test helpers for the course experience.
"""

import datetime

from course_modes.models import CourseMode

TEST_COURSE_PRICE = 50


def add_course_mode(course, upgrade_deadline_expired=False):
    """
    Adds a course mode to the test course.
    """
    upgrade_exp_date = datetime.datetime.now()
    if upgrade_deadline_expired:
        upgrade_exp_date = upgrade_exp_date - datetime.timedelta(days=21)
    else:
        upgrade_exp_date = upgrade_exp_date + datetime.timedelta(days=21)

    CourseMode(
        course_id=course.id,
        mode_slug=CourseMode.VERIFIED,
        mode_display_name="Verified Certificate",
        min_price=TEST_COURSE_PRICE,
        _expiration_datetime=upgrade_exp_date,  # pylint: disable=protected-access
    ).save()
