from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django_future.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response

from xmodule.modulestore.django import modulestore, loc_mapper
from util.json_request import JsonResponse, expect_json
from student.roles import CourseRole, CourseInstructorRole, CourseStaffRole, GlobalStaff
from course_creators.views import user_requested_access

from .access import has_course_access

from student.models import CourseEnrollment
from xmodule.modulestore.locator import BlockUsageLocator
from django.http import HttpResponseNotFound
from student import auth


__all__ = ['request_course_creator', 'course_team_handler']


@require_POST
@login_required
def request_course_creator(request):
    """
    User has requested course creation access.
    """
    user_requested_access(request.user)
    return JsonResponse({"Status": "OK"})


# pylint: disable=unused-argument
@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT", "DELETE"))
def course_team_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None, email=None):
    """
    The restful handler for course team users.

    GET
        html: return html page for managing course team
        json: return json representation of a particular course team member (email is required).
    POST or PUT
        json: modify the permissions for a particular course team member (email is required, as well as role in the payload).
    DELETE:
        json: remove a particular course team member from the course team (email is required).
    """
    location = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
    if not has_course_access(request.user, location):
        raise PermissionDenied()

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        return _course_team_user(request, location, email)
    elif request.method == 'GET':  # assume html
        return _manage_users(request, location)
    else:
        return HttpResponseNotFound()


def _manage_users(request, locator):
    """
    This view will return all CMS users who are editors for the specified course
    """
    old_location = loc_mapper().translate_locator_to_location(locator)

    # check that logged in user has permissions to this item
    if not has_course_access(request.user, locator):
        raise PermissionDenied()

    course_module = modulestore().get_item(old_location)
    instructors = CourseInstructorRole(locator).users_with_role()
    # the page only lists staff and assumes they're a superset of instructors. Do a union to ensure.
    staff = set(CourseStaffRole(locator).users_with_role()).union(instructors)

    return render_to_response('manage_users.html', {
        'context_course': course_module,
        'staff': staff,
        'instructors': instructors,
        'allow_actions': has_course_access(request.user, locator, role=CourseInstructorRole),
    })


@expect_json
def _course_team_user(request, locator, email):
    """
    Handle the add, remove, promote, demote requests ensuring the requester has authority
    """
    # check that logged in user has permissions to this item
    if has_course_access(request.user, locator, role=CourseInstructorRole):
        # instructors have full permissions
        pass
    elif has_course_access(request.user, locator, role=CourseStaffRole) and email == request.user.email:
        # staff can only affect themselves
        pass
    else:
        msg = {
            "error": _("Insufficient permissions")
        }
        return JsonResponse(msg, 400)

    try:
        user = User.objects.get(email=email)
    except Exception:
        msg = {
            "error": _("Could not find user by email address '{email}'.").format(email=email),
        }
        return JsonResponse(msg, 404)

    # role hierarchy: globalstaff > "instructor" > "staff" (in a course)
    if request.method == "GET":
        # just return info about the user
        msg = {
            "email": user.email,
            "active": user.is_active,
            "role": None,
        }
        # what's the highest role that this user has? (How should this report global staff?)
        for role in [CourseInstructorRole(locator), CourseStaffRole(locator)]:
            if role.has_user(user):
                msg["role"] = role.ROLE
                break
        return JsonResponse(msg)

    # can't modify an inactive user
    if not user.is_active:
        msg = {
            "error": _('User {email} has registered but has not yet activated his/her account.').format(email=email),
        }
        return JsonResponse(msg, 400)

    if request.method == "DELETE":
        # remove all roles in this course from this user: but fail if the user
        # is the last instructor in the course team
        instructors = CourseInstructorRole(locator)
        if instructors.has_user(user):
            if instructors.users_with_role().count() == 1:
                msg = {
                    "error": _("You may not remove the last instructor from a course")
                }
                return JsonResponse(msg, 400)
            else:
                instructors.remove_users(request.user, user)

        auth.remove_users(request.user, CourseStaffRole(locator), user)
        return JsonResponse()

    # all other operations require the requesting user to specify a role
    role = request.json.get("role", request.POST.get("role"))
    if role is None:
        return JsonResponse({"error": _("`role` is required")}, 400)

    old_location = loc_mapper().translate_locator_to_location(locator)
    if role == "instructor":
        if not has_course_access(request.user, locator, role=CourseInstructorRole):
            msg = {
                "error": _("Only instructors may create other instructors")
            }
            return JsonResponse(msg, 400)
        auth.add_users(request.user, CourseInstructorRole(locator), user)
        # auto-enroll the course creator in the course so that "View Live" will work.
        CourseEnrollment.enroll(user, old_location.course_id)
    elif role == "staff":
        # add to staff regardless (can't do after removing from instructors as will no longer
        # be allowed)
        auth.add_users(request.user, CourseStaffRole(locator), user)
        # if we're trying to downgrade a user from "instructor" to "staff",
        # make sure we have at least one other instructor in the course team.
        instructors = CourseInstructorRole(locator)
        if instructors.has_user(user):
            if instructors.users_with_role().count() == 1:
                msg = {
                    "error": _("You may not remove the last instructor from a course")
                }
                return JsonResponse(msg, 400)
            else:
                instructors.remove_users(request.user, user)

        # auto-enroll the course creator in the course so that "View Live" will work.
        CourseEnrollment.enroll(user, old_location.course_id)

    return JsonResponse()
