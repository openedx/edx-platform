from datetime import datetime
from logging import getLogger

import pytz
from crum import get_current_request

from course_action_state.models import CourseRerunState
from custom_settings.models import CustomSettings
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.theming.helpers import get_current_request
from openedx.features.course_card.models import CourseCard

log = getLogger(__name__)


def get_course_open_date(course):
    """
    check if course open date is set return that date
    else return course start date
    :param course:
    :return course start date:
    """

    try:
        custom_settings = CustomSettings.objects.get(id=course.id)
        course_open_date = custom_settings.course_open_date
        if course_open_date:
            return course_open_date
        else:
            return course.start
    except CustomSettings.DoesNotExist:
        return course.start


def get_related_card_id(course_id):
    """
    Get course key from parent course
    :param course_id:
    :return:
    """
    course_rerun = CourseRerunState.objects.filter(course_key=course_id).first()
    if course_rerun:
        return course_rerun.source_course_key

    return course_id


def get_related_card(course):
    """
    Get course from parent course
    :param course:
    :return:
    """

    course_rerun = CourseRerunState.objects.filter(course_key=course.id).first()
    if course_rerun:
        return CourseOverview.objects.get(id=course_rerun.source_course_key)

    return course


def get_future_courses(card_id):
    """
        Get future courses for a course
        :param card_id:
        :return:
        """
    utc = pytz.UTC

    other_children_ids = [
        crs.course_key for crs in CourseRerunState.objects.filter(
            source_course_key=card_id, action="rerun", state="succeeded"
        )
    ]
    future_courses = CourseOverview.objects.filter(
        id__in=other_children_ids,
        end__gt=datetime.utcnow().replace(tzinfo=utc)).first()

    return future_courses


def is_course_rereun(course_id):
    """
    Check if the course is created as rerun
    :param course_id:
    :return:
    """
    course_rerun = CourseRerunState.objects.filter(course_key=course_id).first()
    if course_rerun:
        return course_rerun.source_course_key

    return None


def get_course_cards_list():
    request = get_current_request()
    cards_query_set = CourseCard.objects.all() if request.user.is_staff else CourseCard.objects.filter(is_enabled=True)
    course_card_ids = [cc.course_id for cc in cards_query_set]
    courses_list = CourseOverview.objects.select_related('image_set').filter(id__in=course_card_ids)
    return courses_list


def is_course_in_programs(course_id):
    """
    Helper function to check if course is part of program
    @param course_id: course key
    @return: true if course is part of program otherwise false
    """
    programs = get_programs(get_current_request().site)

    for program in programs:
        for program_course in program['courses']:
            if program_course['course_runs']:
                for course_rerun in program_course['course_runs']:
                    if course_rerun['key'] == str(course_id):
                        return True
    return False
