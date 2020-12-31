from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from lms.djangoapps.courseware.courses import (
    get_courses,
    sort_by_announcement,
    sort_by_start_date
)
from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.catalog.utils import get_programs_with_type
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from openedx.features.pakx_features.utils import add_course_progress_and_resume_info_tags_to_enrolled_courses
# Create your views here.


@ensure_csrf_cookie
@login_required
def courses(request):
    """
    Render "find courses" page.  The course selection work is done in courseware.courses.
    """

    courses_list = []
    course_discovery_meanings = getattr(settings, 'COURSE_DISCOVERY_MEANINGS', {})
    if not settings.FEATURES.get('ENABLE_COURSE_DISCOVERY'):
        courses_list = get_courses(request.user)

        if configuration_helpers.get_value("ENABLE_COURSE_SORTING_BY_START_DATE",
                                           settings.FEATURES["ENABLE_COURSE_SORTING_BY_START_DATE"]):
            courses_list = sort_by_start_date(courses_list)
        else:
            courses_list = sort_by_announcement(courses_list)

    # split courses into categories i.e upcoming & in-progress
    in_progress_courses = []
    upcoming_courses = []
    completed_courses = []

    add_course_progress_and_resume_info_tags_to_enrolled_courses(request, courses_list)

    for course in courses_list:
        if course.has_started():
            in_progress_courses.append(course)
        else:
            upcoming_courses.append(course)

    # Add marketable programs to the context.
    programs_list = get_programs_with_type(request.site, include_hidden=False)

    return render_to_response(
        "courseware/courses.html",
        {
            'in_progress_courses': in_progress_courses,
            'upcoming_courses': upcoming_courses,
            'completed_courses': completed_courses,
            'course_discovery_meanings': course_discovery_meanings,
            'programs_list': programs_list,
            'section': 'in-progress'
        }
    )
