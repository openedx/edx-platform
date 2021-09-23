
import logging

from django.db import transaction
from django.http.response import HttpResponseBadRequest, HttpResponseForbidden
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import MultipleObjectsReturned
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from opaque_keys.edx.keys import CourseKey


from lms.djangoapps.instructor import permissions
from lms.djangoapps.courseware.courses import get_course_by_id
from common.djangoapps.util.json_request import JsonResponse
from openedx.features.wikimedia_features.admin_dashboard.admin_task.api_helper import AlreadyRunningError, QueueConnectionError, submit_task
from openedx.features.wikimedia_features.admin_dashboard.tasks import task_calculate_grades_csv

log = logging.getLogger(__name__)
TASK_LOG = logging.getLogger('edx.celery.task')

SUCCESS_MESSAGE_TEMPLATE = _("The {report_type} report is being created. "
                             "To view the status of the report, see Pending Tasks below.")

def require_course_permission(permission):
    """
    Decorator with argument that requires a specific permission of the requesting
    user. If the requirement is not satisfied, returns an
    HttpResponseForbidden (403).

    Assumes that request is in args[0].
    Assumes that course_id is in kwargs['course_id'].
    """
    def decorator(func):
        def wrapped(*args, **kwargs):
            request = args[0]
            courses = kwargs['course_id'].split(",")
            for course in courses:
                course_id  = get_course_by_id(CourseKey.from_string(course))
                if request.user.has_perm(permission, course_id):
                    course_permission = True
                else:
                    return HttpResponseForbidden()
            if course_permission:
                return func(*args, **kwargs)             
        return wrapped
    return decorator

def common_exceptions_400(func):
    """
    Catches common exceptions and renders matching 400 errors.
    (decorator without arguments)
    """

    def wrapped(request, *args, **kwargs):
        use_json = (request.is_ajax() or
                    request.META.get("HTTP_ACCEPT", "").startswith("application/json"))
        try:
            return func(request, *args, **kwargs)
        except User.DoesNotExist:
            message = _('User does not exist.')
        except MultipleObjectsReturned:
            message = _('Found a conflict with given identifier. Please try an alternative identifier')
        except (AlreadyRunningError, QueueConnectionError, AttributeError) as err:
            message = str(err)

        if use_json:
            return HttpResponseBadRequest(message)
        else:
            return HttpResponseBadRequest(message)

    return wrapped

@transaction.non_atomic_requests
@require_POST
@ensure_csrf_cookie
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@require_course_permission(permissions.CAN_RESEARCH)
@common_exceptions_400
def average_calculate_grades_csv(request, course_id):
    """
    AlreadyRunningError is raised if the course's grades are already being updated.
    """
    report_type = _('grade')
    submit_calculate_grades_csv(request, course_id)
    success_status = SUCCESS_MESSAGE_TEMPLATE.format(report_type=report_type)

    return JsonResponse({"status": success_status})

def submit_calculate_grades_csv(request, course_key):
    """
    AlreadyRunningError is raised if the course's grades are already being updated.
    """
    task_type = 'grade_course'
    task_class = task_calculate_grades_csv
    task_input = {}
    task_key = ""

    return submit_task(request, task_type, task_class, course_key, task_input, task_key)
