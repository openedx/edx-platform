import requests
import time

from bridgekeeper.rules import is_staff
from django.http import HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from opaque_keys.edx.locator import CourseLocator

from courseware.courses import get_course_by_id
from canvas_integration.tasks import sync_canvas_enrollments

from remote_gradebook.views import require_course_permission


@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(is_staff)
def add_enrollments_using_canvas(request, course_id):
    """
    Fetches enrollees for a course in a remote gradebook and enrolls those emails in the course in edX
    """
    course_key = CourseLocator.from_string(course_id)
    course = get_course_by_id(course_key)
    if not course.canvas_course_id:
        # TODO: better exception class?
        raise Exception("No canvas_course_id set for course {}".format(course_id))
    sync_canvas_enrollments.delay(course_key=course_id, canvas_course_id=course.canvas_course_id)
    return HttpResponse()
