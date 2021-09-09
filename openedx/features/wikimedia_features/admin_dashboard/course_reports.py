"""
Views for Course Reports
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.util.cache import cache_if_anonymous
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import get_course_by_id, get_courses
from lms.djangoapps.instructor.views.instructor_dashboard import _section_data_download


@login_required
@ensure_csrf_cookie
@cache_if_anonymous()
def course_reports(request):
    courses_list = []
    sections = {"key": {}}
    if not settings.FEATURES.get('ENABLE_COURSE_DISCOVERY'):
        courses_list = get_courses(request.user)
        course = get_course_by_id(courses_list[0].id, depth=0)

        access = {
            'admin': request.user.is_staff,
            'instructor': bool(has_access(request.user, 'instructor', courses_list[0])),
        }
        sections["key"] = _section_data_download(course, access)

    return render_to_response(
        "course_report/course-reports.html",
        {
            'courses': courses_list,
            'section_data': sections,
        }
    )
