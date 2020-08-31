from datetime import datetime
from logging import getLogger

import pytz
from crum import get_current_request
from opaque_keys.edx.keys import CourseKey

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
    if isinstance(course_id, basestring):
        course_id = CourseKey.from_string(course_id)

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


def get_course_cards_list(request=None):
    request = request or get_current_request()
    cards_query_set = CourseCard.objects.all() if request.user.is_staff else CourseCard.objects.filter(is_enabled=True)
    course_card_ids = [cc.course_id for cc in cards_query_set]
    courses_list = CourseOverview.objects.select_related('image_set').filter(id__in=course_card_ids)
    return courses_list


def is_course_in_programs(parent_course_key):
    """
    Helper function to check if course is part of program.

    Parent course(course card) of each rerun is same so we
    just compare with parent of first rerun and check if course
    is part of the program.

    @param parent_course_key: parent course key
    @return: True if parent of first course reruns from discovery matches
             with parent course key
    """
    programs = get_programs(get_current_request().site)

    for program in programs:
        for program_course in program.get('courses', []):
            course_runs = program_course.get('course_runs')
            if course_runs:
                first_rerun = course_runs[0]
                rerun_parent_course_key = get_related_card_id(first_rerun.get('key'))
                if rerun_parent_course_key == parent_course_key:
                    return True
    return False
