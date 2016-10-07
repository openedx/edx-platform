from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from course_creators.views import user_requested_access
from django.http import HttpResponseNotFound
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator
from openedx.core.djangoapps.edxmako.shortcuts import render_to_response
from student import auth
from student.auth import STUDIO_EDIT_ROLES, STUDIO_VIEW_USERS, get_user_permissions
from student.models import CourseEnrollment
from student.roles import CourseInstructorRole, CourseStaffRole, LibraryUserRole
from util.json_request import JsonResponse, expect_json
from xmodule.modulestore.django import modulestore


__all__ = ['request_course_creator', 'course_team_handler']


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
def course_team_handler(request, course_key_string=None, email=None):
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
    course_key = CourseKey.from_string(course_key_string) if course_key_string else None
    # No permissions check here - each helper method does its own check.

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        return _course_team_user(request, course_key, email)
    elif request.method == 'GET':  # assume html
        return _manage_users(request, course_key)
    else:
        return HttpResponseNotFound()


def user_with_role(user, role):
    """ Build user representation with attached role """
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': role
    }


def _manage_users(request, course_key):
    """
    This view will return all CMS users who are editors for the specified course
    """
    # check that logged in user has permissions to this item
    user_perms = get_user_permissions(request.user, course_key)
    if not user_perms & STUDIO_VIEW_USERS:
        raise PermissionDenied()

    course_module = modulestore().get_course(course_key)
    instructors = set(CourseInstructorRole(course_key).users_with_role())
    # the page only lists staff and assumes they're a superset of instructors. Do a union to ensure.
    staff = set(CourseStaffRole(course_key).users_with_role()).union(instructors)

    formatted_users = []
    for user in instructors:
        formatted_users.append(user_with_role(user, 'instructor'))
    for user in staff - instructors:
        formatted_users.append(user_with_role(user, 'staff'))

    return render_to_response('manage_users.html', {
        'context_course': course_module,
        'show_transfer_ownership_hint': request.user in instructors and len(instructors) == 1,
        'users': formatted_users,
        'allow_actions': bool(user_perms & STUDIO_EDIT_ROLES),
    })


@expect_json
def _course_team_user(request, course_key, email):
    """
    Handle the add, remove, promote, demote requests ensuring the requester has authority
    """
    # check that logged in user has permissions to this item
    requester_perms = get_user_permissions(request.user, course_key)
    permissions_error_response = JsonResponse({"error": _("Insufficient permissions")}, 403)
    if (requester_perms & STUDIO_VIEW_USERS) or (email == request.user.email):
        # This user has permissions to at least view the list of users or is editing themself
        pass
    else:
        # This user is not even allowed to know who the authorized users are.
        return permissions_error_response

    try:
        user = User.objects.get(email=email)
    except Exception:
        msg = {
            "error": _("Could not find user by email address '{email}'.").format(email=email),
        }
        return JsonResponse(msg, 404)

    is_library = isinstance(course_key, LibraryLocator)
    # Ordered list of roles: can always move self to the right, but need STUDIO_EDIT_ROLES to move any user left
    if is_library:
        role_hierarchy = (CourseInstructorRole, CourseStaffRole, LibraryUserRole)
    else:
        role_hierarchy = (CourseInstructorRole, CourseStaffRole)

    if request.method == "GET":
        # just return info about the user
        msg = {
            "email": user.email,
            "active": user.is_active,
            "role": None,
        }
        # what's the highest role that this user has? (How should this report global staff?)
        for role in role_hierarchy:
            if role(course_key).has_user(user):
                msg["role"] = role.ROLE
                break
        return JsonResponse(msg)

    # All of the following code is for editing/promoting/deleting users.
    # Check that the user has STUDIO_EDIT_ROLES permission or is editing themselves:
    if not ((requester_perms & STUDIO_EDIT_ROLES) or (user.id == request.user.id)):
        return permissions_error_response

    # can't modify an inactive user
    if not user.is_active:
        msg = {
            "error": _('User {email} has registered but has not yet activated his/her account.').format(email=email),
        }
        return JsonResponse(msg, 400)

    if request.method == "DELETE":
        new_role = None
    else:
        # only other operation supported is to promote/demote a user by changing their role:
        # role may be None or "" (equivalent to a DELETE request) but must be set.
        # Check that the new role was specified:
        if "role" in request.json or "role" in request.POST:
            new_role = request.json.get("role", request.POST.get("role"))
        else:
            return JsonResponse({"error": _("No `role` specified.")}, 400)

    old_roles = set()
    role_added = False
    for role_type in role_hierarchy:
        role = role_type(course_key)
        if role_type.ROLE == new_role:
            if (requester_perms & STUDIO_EDIT_ROLES) or (user.id == request.user.id and old_roles):
                # User has STUDIO_EDIT_ROLES permission or
                # is currently a member of a higher role, and is thus demoting themself
                auth.add_users(request.user, role, user)
                role_added = True
            else:
                return permissions_error_response
        elif role.has_user(user):
            # Remove the user from this old role:
            old_roles.add(role)

    if new_role and not role_added:
        return JsonResponse({"error": _("Invalid `role` specified.")}, 400)

    for role in old_roles:
        if isinstance(role, CourseInstructorRole) and role.users_with_role().count() == 1:
            msg = {"error": _("You may not remove the last Admin. Add another Admin first.")}
            return JsonResponse(msg, 400)
        auth.remove_users(request.user, role, user)

    if new_role and not is_library:
        # The user may be newly added to this course.
        # auto-enroll the user in the course so that "View Live" will work.
        CourseEnrollment.enroll(user, course_key)

    return JsonResponse()
