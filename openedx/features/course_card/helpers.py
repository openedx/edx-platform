from datetime import datetime

import pytz
from course_action_state.models import CourseRerunState
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_card.models import CourseCard


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
    course_card_ids = [cc.course_id for cc in CourseCard.objects.filter(is_enabled=True)]
    courses_list = CourseOverview.objects.select_related('image_set').filter(id__in=course_card_ids)
    return courses_list
