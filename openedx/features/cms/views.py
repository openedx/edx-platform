"""
Views for CMS application
"""
import json
from copy import deepcopy
from datetime import datetime
from logging import getLogger

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import ensure_csrf_cookie
from pytz import utc

from cms.djangoapps.contentstore.views.course import get_courses_accessible_to_user
from contentstore.tasks import rerun_course
from contentstore.utils import add_instructor
from course_action_state.models import CourseRerunState
from edxmako.shortcuts import render_to_response
from openedx.features.course_card.helpers import get_related_card_id
from student.auth import has_studio_write_access
from util.json_request import JsonResponse, expect_json
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore import EdxJSONEncoder
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError

from . import helpers
from .constants import ERROR_MESSAGES

logger = getLogger(__name__)  # pylint: disable=invalid-name


@expect_json
@login_required
@ensure_csrf_cookie
def course_multiple_rerun_handler(request):
    """
    View that handles a creation of multiple course reruns

    Arguments:
        request(HTTPRequest): user request

    Returns:
        create_multiple_rerun (html): view for creating multiple course reruns

    """
    courses, in_process_course_actions = get_courses_accessible_to_user(request)
    in_process_action_course_keys = [uca.course_key for uca in in_process_course_actions]
    courses = [
        course
        for course in courses
        if not isinstance(course, ErrorDescriptor) and (course.id not in in_process_action_course_keys)
    ]

    if request.json:
        course_ids = [str(course.id) for course in courses]
        course_re_run_details = deepcopy(request.json)

        try:
            create_multiple_reruns(course_re_run_details, course_ids, request.user)
        except (ValueError, PermissionDenied) as e:
            logger.error('Multiple rerun creation failed with exception: %s', str(e))
            return JsonResponse(course_re_run_details, encoder=EdxJSONEncoder, status=400)

        return JsonResponse(status=200)

    latest_courses = helpers.latest_course_reruns(courses)

    context = {
        'latest_courses': latest_courses
    }

    return render_to_response('rerun/create_multiple_rerun.html', context)


def create_multiple_reruns(course_re_run_details, course_ids, user):
    """
    Create multiple reruns of a requested course ids

    Arguments:
        course_re_run_details (JSON): A json data of course reruns
        course_ids (list(int)): list of course ids
        user (request.user): user entity object

    Returns:
        ValueError,PermissionDenied: In case of error.
    """

    for course in course_re_run_details:
        for re_run in course['runs']:
            start = '{}-{}'.format(re_run['start_date'], re_run['start_time'])
            try:
                re_run['start'] = datetime.strptime(start, '%m/%d/%Y-%H:%M').replace(tzinfo=utc)
            except ValueError:
                helpers.raise_rerun_creation_exception(re_run, ERROR_MESSAGES['start_date_format_mismatch'],
                                                       exception_class=ValueError)

        if course['source_course_key'] not in course_ids:
            helpers.raise_rerun_creation_exception(course, ERROR_MESSAGES['course_key_not_found'],
                                                   exception_class=ValueError)

    course_re_run_details = helpers.update_course_re_run_details(course_re_run_details)

    re_runs = []

    for course in course_re_run_details:
        for rerun in course['runs']:
            fields = dict()

            fields['display_name'] = course['display_name']
            fields['start'] = rerun['start']
            fields['wiki_slug'] = u"{0}.{1}.{2}".format(course['org'], course['number'], rerun['run'])
            fields['advertised_start'] = None

            # verify user has access to the original course
            if not has_studio_write_access(user, course['source_course_key']):
                helpers.raise_rerun_creation_exception(course, ERROR_MESSAGES['unauthorized_user'],
                                                       exception_class=PermissionDenied)

            # create destination course key
            store = modulestore()
            with store.default_store('split'):
                destination_course_key = store.make_course_key(course['org'], course['number'], rerun['run'])

            # verify org course and run don't already exist
            if store.has_course(destination_course_key, ignore_case=True):
                helpers.raise_rerun_creation_exception(rerun, ERROR_MESSAGES['duplicate_course_id'])
                raise DuplicateCourseError(course['source_course_key'], destination_course_key)

            # Prepare a rerun creation arguments list
            re_runs.append({
                'source_course_key': course['source_course_key'],
                'destination_course_key': destination_course_key,
                'user': user,
                'fields': fields
            })

    # Since the loop contains raise, if there were errors in re-run creation code would have exited.
    for re_run_arguments in re_runs:
        _rerun_course(**re_run_arguments)


def _rerun_course(source_course_key, destination_course_key, user, fields):
    """
    Reruns an existing course.
    """
    # Make sure user has instructor and staff access to the destination course
    # so the user can see the updated status for that course
    add_instructor(destination_course_key, user, user)

    parent_course_key = get_related_card_id(source_course_key)

    # Mark the action as initiated
    CourseRerunState.objects.initiated(parent_course_key, destination_course_key, user, fields['display_name'])

    # Rerun the course as a new celery task
    json_fields = json.dumps(fields, cls=EdxJSONEncoder)
    rerun_course.delay(unicode(source_course_key), unicode(destination_course_key), user.id, json_fields)
