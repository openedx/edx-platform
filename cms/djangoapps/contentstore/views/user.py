from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django_future.csrf import ensure_csrf_cookie
from mitxmako.shortcuts import render_to_response
from django.core.context_processors import csrf

from xmodule.modulestore.django import modulestore
from contentstore.utils import get_url_reverse, get_lms_link_for_item
from util.json_request import expect_json, JsonResponse
from auth.authz import STAFF_ROLE_NAME, INSTRUCTOR_ROLE_NAME, get_users_in_course_group_by_role
from auth.authz import get_user_by_email, add_user_to_course_group, remove_user_from_course_group
from course_creators.views import get_course_creator_status, add_user_with_status_unrequested, user_requested_access

from .access import has_access


@login_required
@ensure_csrf_cookie
def index(request):
    """
    List all courses available to the logged in user
    """
    courses = modulestore('direct').get_items(['i4x', None, None, 'course', None])

    # filter out courses that we don't have access too
    def course_filter(course):
        return (has_access(request.user, course.location)
                # TODO remove this condition when templates purged from db
                and course.location.course != 'templates'
                and course.location.org != ''
                and course.location.course != ''
                and course.location.name != '')
    courses = filter(course_filter, courses)

    return render_to_response('index.html', {
        'courses': [(course.display_name,
                    get_url_reverse('CourseOutline', course),
                    get_lms_link_for_item(course.location, course_id=course.location.course_id))
                    for course in courses],
        'user': request.user,
        'request_course_creator_url': reverse('request_course_creator'),
        'course_creator_status': _get_course_creator_status(request.user),
        'csrf': csrf(request)['csrf_token']
    })


@require_POST
@login_required
def request_course_creator(request):
    """
    User has requested course creation access.
    """
    user_requested_access(request.user)
    return JsonResponse({"Status": "OK"})


@login_required
@ensure_csrf_cookie
def manage_users(request, location):
    '''
    This view will return all CMS users who are editors for the specified course
    '''
    # check that logged in user has permissions to this item
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME) and not has_access(request.user, location, role=STAFF_ROLE_NAME):
        raise PermissionDenied()

    course_module = modulestore().get_item(location)

    return render_to_response('manage_users.html', {
        'context_course': course_module,
        'staff': get_users_in_course_group_by_role(location, STAFF_ROLE_NAME),
        'add_user_postback_url': reverse('add_user', args=[location]).rstrip('/'),
        'remove_user_postback_url': reverse('remove_user', args=[location]).rstrip('/'),
        'allow_actions': has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME),
        'request_user_id': request.user.id
    })


@expect_json
@login_required
@ensure_csrf_cookie
def add_user(request, location):
    '''
    This POST-back view will add a user - specified by email - to the list of editors for
    the specified course
    '''
    email = request.POST.get("email")

    if not email:
        msg = {
            'Status': 'Failed',
            'ErrMsg': _('Please specify an email address.'),
        }
        return JsonResponse(msg, 400)

    # remove leading/trailing whitespace if necessary
    email = email.strip()

    # check that logged in user has admin permissions to this course
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME):
        raise PermissionDenied()

    user = get_user_by_email(email)

    # user doesn't exist?!? Return error.
    if user is None:
        msg = {
            'Status': 'Failed',
            'ErrMsg': _("Could not find user by email address '{email}'.").format(email=email),
        }
        return JsonResponse(msg, 404)

    # user exists, but hasn't activated account?!?
    if not user.is_active:
        msg = {
            'Status': 'Failed',
            'ErrMsg': _('User {email} has registered but has not yet activated his/her account.').format(email=email),
        }
        return JsonResponse(msg, 400)

    # ok, we're cool to add to the course group
    add_user_to_course_group(request.user, user, location, STAFF_ROLE_NAME)

    return JsonResponse({"Status": "OK"})


@expect_json
@login_required
@ensure_csrf_cookie
def remove_user(request, location):
    '''
    This POST-back view will remove a user - specified by email - from the list of editors for
    the specified course
    '''

    email = request.POST["email"]

    # check that logged in user has admin permissions on this course
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME):
        raise PermissionDenied()

    user = get_user_by_email(email)
    if user is None:
        msg = {
            'Status': 'Failed',
            'ErrMsg': _("Could not find user by email address '{email}'.").format(email=email),
        }
        return JsonResponse(msg, 404)

    # make sure we're not removing ourselves
    if user.id == request.user.id:
        raise PermissionDenied()

    remove_user_from_course_group(request.user, user, location, STAFF_ROLE_NAME)

    return JsonResponse({"Status": "OK"})


def _get_course_creator_status(user):
    """
    Helper method for returning the course creator status for a particular user,
    taking into account the values of DISABLE_COURSE_CREATION and ENABLE_CREATOR_GROUP.

    If the user passed in has not previously visited the index page, it will be
    added with status 'unrequested' if the course creator group is in use.
    """
    if user.is_staff:
        course_creator_status = 'granted'
    elif settings.MITX_FEATURES.get('DISABLE_COURSE_CREATION', False):
        course_creator_status = 'disallowed_for_this_site'
    elif settings.MITX_FEATURES.get('ENABLE_CREATOR_GROUP', False):
        course_creator_status = get_course_creator_status(user)
        if course_creator_status is None:
            # User not grandfathered in as an existing user, has not previously visited the dashboard page.
            # Add the user to the course creator admin table with status 'unrequested'.
            add_user_with_status_unrequested(user)
            course_creator_status = get_course_creator_status(user)
    else:
        course_creator_status = 'granted'

    return course_creator_status
