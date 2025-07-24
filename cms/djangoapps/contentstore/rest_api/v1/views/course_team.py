"""
API Views for course team.
"""

import edx_api_doc_tools as apidocs
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.contentstore.utils import get_course_team
from common.djangoapps.student.auth import STUDIO_VIEW_USERS, get_user_permissions
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.models.user import CourseAccessRole
from common.djangoapps.student.roles import CourseRole
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, verify_course_exists, view_auth_classes

from ..serializers import CourseTeamManagementSerializer, CourseTeamSerializer

User = get_user_model()


@view_auth_classes(is_authenticated=True)
class CourseTeamView(DeveloperErrorViewMixin, APIView):
    """
    View for getting data for course team.
    """

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "course_id", apidocs.ParameterLocation.PATH, description="Course ID"
            ),
        ],
        responses={
            200: CourseTeamSerializer,
            401: "The requester is not authenticated.",
            403: "The requester cannot access the specified course.",
            404: "The requested course does not exist.",
        },
    )
    @verify_course_exists()
    def get(self, request: Request, course_id: str):
        """
        Get all CMS users who are editors for the specified course.

        **Example Request**

            GET /api/contentstore/v1/course_team/{course_id}

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains keys that
        are the course's team info.

        **Example Response**

        ```json
        {
            "show_transfer_ownership_hint": true,
            "users": [
                {
                    "email": "edx@example.com",
                    "id": "3",
                    "role": "instructor",
                    "username": "edx"
                },
            ],
            "allow_actions": true
        }
        ```
        """
        user = request.user
        course_key = CourseKey.from_string(course_id)

        user_perms = get_user_permissions(user, course_key)
        if not user_perms & STUDIO_VIEW_USERS:
            self.permission_denied(request)

        course_team_context = get_course_team(user, course_key, user_perms)
        serializer = CourseTeamSerializer(course_team_context)
        return Response(serializer.data)


class CourseTeamManagementAPIView(GenericAPIView):
    """
    Use case:
        - APIs for viewing and managing a user's course team roles.
        - Lists courses where the authenticated user has permission to manage roles.
        - Displays the given user's role in each accessible course.
        - Allows assigning or revoking roles via PUT, limited to courses the user can manage.
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = CourseTeamManagementSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._course_role_map = {}
        self._access_roles = None

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "email",
                apidocs.ParameterLocation.QUERY,
                description="User's email address (required)",
            ),
        ],
        responses={
            200: CourseTeamManagementSerializer,
            400: "Missing required query parameters. 'email' is required.",
            401: "The requester is not authenticated.",
            403: "The requester is not an admin.",
            404: "The requested user does not exist.",
        },
    )
    def get_serializer_context(self):
        """Provide extra context to the serializer."""
        context = super().get_serializer_context()
        context["course_role_map"] = getattr(self, "_course_role_map", {})
        return context

    def get_course_role_map_for_user(self, user):
        """Return a mapping of course_id to role for staff/instructor roles of given user."""
        access_roles = CourseAccessRole.objects.filter(
            user=user, role__in=["staff", "instructor"]
        )
        course_role_map = {}
        for ar in access_roles:
            cid = str(ar.course_id)
            # Prioritize instructor role if present
            if ar.role == "instructor" or cid not in course_role_map:
                course_role_map[cid] = ar.role
        return course_role_map

    def get_accessible_courses_for_user(self, auth_user):
        """Return queryset of courses accessible by the authenticated user."""
        if auth_user.is_superuser or auth_user.is_staff:
            return CourseOverview.objects.all()

        access_roles = CourseAccessRole.objects.filter(
            user=auth_user, role="instructor"
        ).only("org", "course_id")

        # Collect org-level and course-level permissions
        orgs = set()
        course_keys = set()

        for ar in access_roles:
            if ar.course_id:
                course_keys.add(str(ar.course_id))
            elif ar.org:
                orgs.add(ar.org)

        # Build a filter to fetch all courses:
        # - Courses in the orgs where the user has org-level access
        # - Courses explicitly assigned to the user
        course_filter = Q()
        if orgs:
            course_filter |= Q(org__in=orgs)
        if course_keys:
            course_filter |= Q(id__in=course_keys)

        return (
            CourseOverview.objects.filter(course_filter)
            if course_filter
            else CourseOverview.objects.none()
        )

    def get_queryset(self):
        """Main entry to return courses filtered by authenticated user access and requested user roles."""
        email = self.request.query_params.get("email")
        if not email:
            raise ValidationError(
                {"detail": "Missing required query parameters. 'email' is required."}
            )

        try:
            user = User.objects.get(email=email, is_active=True)
        except ObjectDoesNotExist as exc:
            raise NotFound(
                f"User with email '{email}' not found or not active."
            ) from exc

        self._access_roles = CourseAccessRole.objects.filter(
            user=user, role__in=["staff", "instructor"]
        )
        self._course_role_map = self.get_course_role_map_for_user(user)

        auth_user = self.request.user
        return self.get_accessible_courses_for_user(auth_user)

    def list(self, request, *args, **kwargs):
        """list of courses for the organization and user."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get(self, request, *args, **kwargs):
        """
        Use case:
            GET API to retrieve a list of courses accessible by the authenticated user,
            along with the specified user's role ("instructor", "staff", or null) in each course.

        Endpoint:
            GET /api/contentstore/v1/course_team/manage?email=<user_email>

        Query Parameters:
            email: Email address of the user whose roles are being queried (required).

        Returns:
            List of courses accessible to the authenticated user, each annotated with the
            specified user's role in that course.

        Example Response:
            {
                "results": [
                    {
                        "course_id": "course-v1:edX+DemoX+2025_T1",
                        "course_name": "edX Demonstration Course",
                        "role": "instructor"
                    },
                    ...
                ]
            }
        """
        return self.list(request, *args, **kwargs)

    @apidocs.schema(
        responses={
            200: "Roles updated successfully.",
            400: "Invalid request data.",
            401: "The requester is not authenticated.",
            403: "The requester is not an admin.",
        },
    )
    def put(self, request, *args, **kwargs):
        """
        Bulk assign or revoke course team roles for users across multiple courses.

        **Permissions:**
            - Admin/Staff users: Can manage roles for any course
            - Instructor users: Can only manage roles for courses/orgs they have instructor access to
            - Other users: Access denied

        **Endpoint:**
            PUT /api/contentstore/v1/course_team/manage

        **Request Data:**
            A JSON list of dicts, each containing:
                - email: User's email address
                - course_id: Course key string
                - role: Role to assign or revoke ("instructor" or "staff")
                - action: "assign" or "revoke"

        **Example Request**
        ```json
        [
            {
                "email": "user1@example.com",
                "course_id": "course-v1:edX+DemoX+2025_T1",
                "role": "instructor",
                "action": "assign"
            },
            {
                "email": "user2@example.com",
                "course_id": "course-v1:edX+DemoX+2025_T2",
                "role": "instructor",
                "action": "revoke"
            }
        ]
        ```

        **Returns:**
            - HTTP 200 with per-entry results for each operation (success or error details)
            - HTTP 400 if the request data is not a non-empty list

        **Example Response**
        ```json
        {
            "results": [
                {
                    "email": "user1@example.com",
                    "course_id": "course-v1:edX+DemoX+2025_T1",
                    "role": "instructor",
                    "action": "assign",
                    "status": "success"
                },
                {
                    "email": "user2@example.com",
                    "course_id": "course-v1:edX+DemoX+2025_T2",
                    "role": "instructor",
                    "action": "revoke",
                    "status": "failed",
                    "error": "User not found."
                }
            ]
        }
        ```
        """
        results = []

        # Validate request data type
        if not isinstance(request.data, list) or not request.data:
            return Response(
                {
                    "results": [
                        {
                            "status": "failed",
                            "error": "Request data must be a non-empty list of role assignment objects.",
                        }
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        auth_user = request.user

        # Get accessible orgs/courses or permission error response
        accessible_orgs, accessible_courses, permission_error = (
            self._fetch_user_accessible_orgs_and_courses(auth_user)
        )
        if permission_error:
            return permission_error

        user_cache = {}
        course_key_cache = {}

        for data in request.data:
            result = self._handle_role_assignment_entry(
                data,
                auth_user,
                accessible_orgs,
                accessible_courses,
                user_cache,
                course_key_cache,
            )
            results.append(result)

        return Response({"results": results}, status=status.HTTP_200_OK)

    def _fetch_user_accessible_orgs_and_courses(self, auth_user):
        """Return (orgs, courses, error_response) based on user permissions."""
        accessible_orgs = set()
        accessible_courses = set()
        permission_error = None

        # Admins and staff have full access by default
        if not (auth_user.is_superuser or auth_user.is_staff):
            roles = CourseAccessRole.objects.filter(
                user=auth_user, role="instructor"
            ).only("org", "course_id")

            if roles.exists():
                for role in roles:
                    if role.course_id:
                        accessible_courses.add(str(role.course_id))
                    elif role.org:
                        accessible_orgs.add(role.org)
            else:
                permission_error = Response(
                    {
                        "results": [
                            {
                                "status": "failed",
                                "error": "You do not have permission to perform bulk role operations.",
                            }
                        ]
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        return accessible_orgs, accessible_courses, permission_error

    def _handle_role_assignment_entry(
        self,
        data,
        auth_user,
        accessible_orgs,
        accessible_courses,
        user_cache,
        course_key_cache,
    ):
        """Validate and perform the action for a single data entry."""

        email = data.get("email")
        course_id = data.get("course_id")
        role = data.get("role")
        action = data.get("action")

        # Validate required fields
        if not all([email, course_id, role, action]):
            return self._make_result(
                data,
                outcome="failed",
                error="Missing required fields: 'email', 'course_id', 'role', and 'action' are all required.",
            )

        # Validate role field
        if role not in {"instructor", "staff"}:
            return self._make_result(
                data, "failed", "Invalid role. Must be 'instructor' or 'staff'."
            )

        # Fetch course key, using cache to minimize DB queries
        course_key = self._get_course_key(course_id, course_key_cache)
        if not course_key:
            return self._make_result(data, "failed", "Invalid course_id.")

        # Ensure only admin/staff or authorized instructors can manage roles for this course/org
        if not (auth_user.is_staff or auth_user.is_superuser) and (
            course_id not in accessible_courses
            and course_key.org not in accessible_orgs
        ):
            return self._make_result(
                data,
                "failed",
                f"You do not have instructor access to course '{course_id}' or org '{course_key.org}'.",
            )

        # Fetch user, using cache to minimize DB queries
        user = self._get_user(email, user_cache)
        if not user:
            return self._make_result(data, "failed", "User not found.")

        if not user.is_active:
            return self._make_result(data, "failed", "User is not active.")

        # Perform role update based on action
        return self._perform_role_action(data, role, action, user, course_key)

    def _get_course_key(self, course_id, cache):
        """Fetch or get cached CourseKey."""
        if course_id in cache:
            return cache[course_id]

        try:
            course_key = CourseKey.from_string(course_id)
        except Exception as exc:  # pylint: disable=broad-except
            course_key = None

        cache[course_id] = course_key
        return course_key

    def _get_user(self, email, cache):
        """Fetch or get cached user by email."""
        if email in cache:
            return cache[email]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        cache[email] = user
        return user

    def _perform_role_action(self, data, role, action, user, course_key):
        """Assign or revoke role for the user on the course."""
        try:
            course_role = CourseRole(role, course_key)
            if action == "assign":
                course_role.add_users(user)
                CourseEnrollment.enroll(user, course_key)
            elif action == "revoke":
                course_role.remove_users(user)
            else:
                return self._make_result(
                    data, "failed", "Invalid action. Use 'assign' or 'revoke'."
                )
            return self._make_result(data, "success")
        except Exception as exc:  # pylint: disable=broad-except
            return self._make_result(data, "failed", str(exc))

    def _make_result(self, data, outcome, error=None):
        """
        Formats the response for each role assignment entry.
        """
        result = {
            "email": data.get("email"),
            "course_id": data.get("course_id"),
            "role": data.get("role"),
            "action": data.get("action"),
            "status": outcome,
        }
        if error:
            result["error"] = error
        return result
