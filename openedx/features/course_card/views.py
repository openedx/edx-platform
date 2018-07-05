from datetime import datetime

import pytz
from course_action_state.models import CourseRerunState
from openedx.core.djangoapps.timed_notification.core import get_course_first_chapter_link
from philu_overrides.helpers import get_user_current_enrolled_class
from student.models import CourseEnrollment
from edxmako.shortcuts import render_to_response
from openedx.features.course_card.models import CourseCard
from django.views.decorators.csrf import csrf_exempt
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

utc = pytz.UTC


def get_course_start_date(course):
    """
    this function takes course and returns start date of the project
    if start and end dates are set and start date is in future
    :param course:
    :return Course start date:
    """

    current_time = datetime.utcnow().replace(tzinfo=utc)
    course_start_time = None

    if course and course.start and course.end:
        _start_time = course.start.replace(tzinfo=utc)
        if _start_time >= current_time:
            course_start_time = course.start

    return course_start_time


@csrf_exempt
def get_course_cards(request):
    """
    :param request:
    :return: list of active cards
    """

    course_card_ids = [cc.course_id for cc in CourseCard.objects.filter(is_enabled=True)]
    courses_list = CourseOverview.objects.select_related('image_set').filter(id__in=course_card_ids)
    current_time = datetime.now()

    date_time_format = '%b %-d, %Y'

    for course in courses_list:
        course.start_date = None
        course_rerun_states = [crs.course_key for crs in CourseRerunState.objects.filter(
            source_course_key=course.id, action="rerun", state="succeeded")]

        course_rerun_object = CourseOverview.objects.select_related('image_set').filter(
            id__in=course_rerun_states, start__gte=current_time).order_by('start').first()

        course_start_time = get_course_start_date(course)
        rerun_start_time = get_course_start_date(course_rerun_object)

        if course_start_time and rerun_start_time:
            if course_start_time < rerun_start_time:
                course.start_date = course_start_time.strftime(date_time_format)
            else:
                course.start_date = rerun_start_time.strftime(date_time_format)

        elif course_start_time:
            course.start_date = course_start_time.strftime(date_time_format)

        elif rerun_start_time:
            course.start_date = rerun_start_time.strftime(date_time_format)

        current_class, user_current_enrolled_class, current_enrolled_class_target = get_user_current_enrolled_class(
            request, course)

        if current_class:
            course.start_date = current_class.start.strftime(date_time_format)

        if user_current_enrolled_class:
            course.is_enrolled = True
            course.course_target = current_enrolled_class_target

    return render_to_response(
        "course_card/courses.html",
        {
            'courses': courses_list
        }
    )

