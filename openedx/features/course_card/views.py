from datetime import datetime

import pytz
from openedx.core.djangoapps.timed_notification.core import get_course_first_chapter_link
from student.models import CourseEnrollment
from edxmako.shortcuts import render_to_response
from openedx.features.course_card.models import CourseCard
from django.views.decorators.csrf import csrf_exempt
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


@csrf_exempt
def get_course_cards(request):
    """
    :param request:
    :return: list of active cards
    """

    course_card_ids = [cc.course_id for cc in CourseCard.objects.filter(is_enabled=True)]
    courses_list = CourseOverview.objects.filter(id__in=course_card_ids)
    current_time = datetime.now()

    ids_filter = ",".join(["'" + cl.id.__str__() + "'" for cl in courses_list])

    qry = "select *, min(co.start) as start_date from course_overviews_courseoverview co " \
          "inner join course_action_state_coursererunstate crs on co.id = crs.course_key " \
          "where crs.source_course_key in (" + ids_filter + ") " \
          "and co.end >= " + current_time.strftime('%Y-%m-%d') + " group by co.id"

    course_rerun_views = CourseOverview.objects.raw(qry)

    utc = pytz.UTC
    current_course = None

    for course in courses_list:
        course_start_time = None
        if course.start:
            course_start_time = course.start.replace(tzinfo=utc)
        if course_start_time and course_start_time > datetime.utcnow().replace(tzinfo=utc):
            start_date = course.start
            current_course = course
        else:
            start_date = None
        for re_run in course_rerun_views:
            if course.id.__str__() == re_run.source_course_key:
                if start_date and start_date <= re_run.start:
                    start_date = start_date
                else:
                    start_date = re_run.start
                    current_course = re_run

        course.start_date = None if not start_date else start_date.strftime('%b %-d, %Y')
        is_enrolled = CourseEnrollment.is_enrolled(request.user, current_course.id)
        course.is_enrolled = is_enrolled
        course_target = get_course_first_chapter_link(current_course, request)
        course.course_target = course_target
    return render_to_response(
        "course_card/courses.html",
        {
            'courses': courses_list
        }
    )

