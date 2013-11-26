import json
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django_future.csrf import ensure_csrf_cookie
from mitxmako.shortcuts import render_to_response

from xmodule.modulestore.django import modulestore, loc_mapper
from util.json_request import JsonResponse
from auth.authz import (
    STAFF_ROLE_NAME, INSTRUCTOR_ROLE_NAME, get_course_groupname_for_role)
from course_creators.views import user_requested_access

from .access import has_access
from django.http import HttpResponseRedirect
from student.models import (UserProfile)
from student.models import CourseEnrollment
from xmodule.modulestore.locator import BlockUsageLocator
from django.http import HttpResponseNotFound


__all__ = ['request_course_creator', 'course_team_handler']

@ensure_csrf_cookie
def new_user_social(request):
    if not request.user.is_authenticated():

        return HttpResponseRedirect('signin')
    try:
        userprofile=UserProfile(user=request.user)
        userprofile.save()
    except:
        return JsonResponse({"error": _("malformed JSON")}, 400)

    return HttpResponseRedirect('howitworks')


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
@require_http_methods(("GET", "POST", "PUT", "DELETE"))
def course_team_handler(request, tag=None, course_id=None, branch=None, version_guid=None, block=None, email=None):
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
    location = BlockUsageLocator(course_id=course_id, branch=branch, version_guid=version_guid, usage_id=block)
    if not has_access(request.user, location):
        raise PermissionDenied()

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        return _course_team_user(request, location, email)
    elif request.method == 'GET':  # assume html
        return _manage_users(request, location)
    else:
        return HttpResponseNotFound()


def _manage_users(request, location):
    """
    This view will return all CMS users who are editors for the specified course
    """
    old_location = loc_mapper().translate_locator_to_location(location)

    # check that logged in user has permissions to this item
    if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME) and not has_access(request.user, location, role=STAFF_ROLE_NAME):
        raise PermissionDenied()

    course_module = modulestore().get_item(old_location)

    staff_groupname = get_course_groupname_for_role(location, "staff")
    staff_group, __ = Group.objects.get_or_create(name=staff_groupname)
    inst_groupname = get_course_groupname_for_role(location, "instructor")
    inst_group, __ = Group.objects.get_or_create(name=inst_groupname)

    return render_to_response('manage_users.html', {
        'context_course': course_module,
        'staff': staff_group.user_set.all(),
        'instructors': inst_group.user_set.all(),
        'allow_actions': has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME),
    })


def _course_team_user(request, location, email):
    old_location = loc_mapper().translate_locator_to_location(location)
    # check that logged in user has permissions to this item
    if has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME):
        # instructors have full permissions
        pass
    elif has_access(request.user, location, role=STAFF_ROLE_NAME) and email == request.user.email:
        # staff can only affect themselves
        pass
    else:
        msg = {
            "error": _("Insufficient permissions")
        }
        return JsonResponse(msg, 400)

    try:
        user = User.objects.get(email=email)
    except:
        msg = {
            "error": _("Could not find user by email address '{email}'.").format(email=email),
        }
        return JsonResponse(msg, 404)

    # role hierarchy: "instructor" has more permissions than "staff" (in a course)
    roles = ["instructor", "staff"]

    if request.method == "GET":
        # just return info about the user
        msg = {
            "email": user.email,
            "active": user.is_active,
            "role": None,
        }
        # what's the highest role that this user has?
        groupnames = set(g.name for g in user.groups.all())
        for role in roles:
            role_groupname = get_course_groupname_for_role(old_location, role)
            if role_groupname in groupnames:
                msg["role"] = role
                break
        return JsonResponse(msg)

    # can't modify an inactive user
    if not user.is_active:
        msg = {
            "error": _('User {email} has registered but has not yet activated his/her account.').format(email=email),
        }
        return JsonResponse(msg, 400)

    # make sure that the role groups exist
    groups = {}
    for role in roles:
        groupname = get_course_groupname_for_role(old_location, role)
        group, __ = Group.objects.get_or_create(name=groupname)
        groups[role] = group

    if request.method == "DELETE":
        # remove all roles in this course from this user: but fail if the user
        # is the last instructor in the course team
        instructors = set(groups["instructor"].user_set.all())
        staff = set(groups["staff"].user_set.all())
        if user in instructors and len(instructors) == 1:
            msg = {
                "error": _("You may not remove the last instructor from a course")
            }
            return JsonResponse(msg, 400)

        if user in instructors:
            user.groups.remove(groups["instructor"])
        if user in staff:
            user.groups.remove(groups["staff"])
        user.save()
        return JsonResponse()

    # all other operations require the requesting user to specify a role
    if request.META.get("CONTENT_TYPE", "").startswith("application/json") and request.body:
        try:
            payload = json.loads(request.body)
        except:
            return JsonResponse({"error": _("malformed JSON")}, 400)
        try:
            role = payload["role"]
        except KeyError:
            return JsonResponse({"error": _("`role` is required")}, 400)
    else:
        if not "role" in request.POST:
            return JsonResponse({"error": _("`role` is required")}, 400)
        role = request.POST["role"]

    if role == "instructor":
        if not has_access(request.user, location, role=INSTRUCTOR_ROLE_NAME):
            msg = {
                "error": _("Only instructors may create other instructors")
            }
            return JsonResponse(msg, 400)
        user.groups.add(groups["instructor"])
        user.save()
        # auto-enroll the course creator in the course so that "View Live" will work.
        CourseEnrollment.enroll(user, old_location.course_id)
    elif role == "staff":
        # if we're trying to downgrade a user from "instructor" to "staff",
        # make sure we have at least one other instructor in the course team.
        instructors = set(groups["instructor"].user_set.all())
        if user in instructors:
            if len(instructors) == 1:
                msg = {
                    "error": _("You may not remove the last instructor from a course")
                }
                return JsonResponse(msg, 400)
            user.groups.remove(groups["instructor"])
        user.groups.add(groups["staff"])
        user.save()
        # auto-enroll the course creator in the course so that "View Live" will work.
        CourseEnrollment.enroll(user, old_location.course_id)

    return JsonResponse()

