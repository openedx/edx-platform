from six import text_type
from django.conf import settings
from lms.djangoapps.courseware.courses import (
    can_self_enroll_in_course,
    course_open_for_self_enrollment,
    get_course,
    get_course_date_blocks,
    get_course_overview_with_access,
    get_course_with_access,
    get_courses,
    get_current_child,
    get_permission_for_course_about,
    get_studio_url,
    sort_by_announcement,
    sort_by_start_date
)
from student.models import CourseEnrollment
from edxmako.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from openedx.core.djangoapps.catalog.utils import get_programs, get_programs_with_type
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.features.course_experience.utils import (get_course_outline_block_tree,
                                                      get_resume_block)
# Create your views here.


def add_resume_link_for_enrolled_course(request, course, allow_start_dates_in_future=False):
    """
    adds information relevant to resume course functionality to the given course model

    :param request: (HttpRequest) request object
    :param course: (CourseView) course view model object
    :param allow_start_dates_in_future: (bool) When True, will allow blocks to be
            returned that can bypass the StartDateTransformer's filter to show
            blocks with start dates in the future.

    has_visited_course: True if the user has ever visited the course, False otherwise.
    resume_course_url: The URL of the 'resume course' block if the user has visited the course,
                        otherwise the URL of the course root.
    resume_course_title: The display_name of the resume course block, otherwise the display_name of course root

    """
    course_id = text_type(course.id)
    course_outline_root_block = get_course_outline_block_tree(request, course_id, request.user,
                                                              allow_start_dates_in_future)
    resume_block = get_resume_block(course_outline_root_block) if course_outline_root_block else None
    has_visited_course = bool(resume_block)
    if resume_block:
        resume_course_url = resume_block['lms_web_url']
        resume_course_title = resume_block['display_name']
    else:
        resume_course_url = course_outline_root_block['lms_web_url'] if course_outline_root_block else None
        resume_course_title = course_outline_root_block['display_name'] if course_outline_root_block else None

    course.has_visited_course = has_visited_course
    course.resume_course_url = resume_course_url
    course.resume_course_title = resume_course_title


def add_tag_to_enrolled_courses(request, courses_list):
    """
    Adds a tag enrolled to the course in which user is enrolled

    :param request: (HttpRequest) request object
    :param courses_list: [CourseView] list of course view objects
    """
    for course in courses_list:
        if CourseEnrollment.is_enrolled(request.user, course.id):
            add_resume_link_for_enrolled_course(request, course, True)
            course.enrolled = True
        else:
            course.enrolled = False


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

    add_tag_to_enrolled_courses(request, courses_list)

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
