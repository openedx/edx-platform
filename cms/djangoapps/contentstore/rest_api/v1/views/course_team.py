""" API Views for course team """

import edx_api_doc_tools as apidocs
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from opaque_keys.edx.keys import CourseKey
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.contentstore.rest_api.pagination import CustomPagination
from cms.djangoapps.contentstore.utils import get_course_team
from common.djangoapps.student.auth import STUDIO_VIEW_USERS, get_user_permissions
from common.djangoapps.student.models.user import CourseAccessRole
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
            apidocs.string_parameter("course_id", apidocs.ParameterLocation.PATH, description="Course ID"),
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
        - Allows platform admins to audit or review a user's access level across all courses in an organization.
        - Useful for compliance, support, or bulk role management tools.
    """

    permission_classes = (IsAdminUser,)
    pagination_class = CustomPagination
    serializer_class = CourseTeamManagementSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._course_role_map = {}
        self._user = None
        self._access_roles = None

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "org",
                apidocs.ParameterLocation.QUERY,
                description="Organization code (required)",
            ),
            apidocs.string_parameter(
                "email",
                apidocs.ParameterLocation.QUERY,
                description="User's email address (required)",
            ),
            apidocs.string_parameter(
                "page",
                apidocs.ParameterLocation.QUERY,
                description="Page number for pagination.",
            ),
            apidocs.string_parameter(
                "page_size",
                apidocs.ParameterLocation.QUERY,
                description="Number of results per page.",
            ),
        ],
        responses={
            200: CourseTeamManagementSerializer,
            400: "Missing required query parameters. Both 'org' and 'email' are required.",
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

    def get_queryset(self):
        """Return queryset of courses for the given org and user email."""
        org = self.request.query_params.get("org")
        email = self.request.query_params.get("email")
        if not org or not email:
            raise ValidationError(
                {
                    "detail": "Missing required query parameters. Both 'org' and 'email' are required."
                }
            )

        try:
            self._user = User.objects.get(email=email)
        except ObjectDoesNotExist as exc:
            raise NotFound(f"User with email '{email}' not found.") from exc

        self._access_roles = CourseAccessRole.objects.filter(
            user=self._user, org=org, role__in=["staff", "instructor"]
        )

        course_role_map = {}
        for ar in self._access_roles:
            cid = str(ar.course_id)
            if ar.role == "instructor" or cid not in course_role_map:
                course_role_map[cid] = ar.role
        self._course_role_map = course_role_map
        qs = CourseOverview.objects.filter(org=org)
        return qs

    def list(self, request, *args, **kwargs):
        """Paginated list of courses for the organization and user."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get(self, request, *args, **kwargs):
        """
        GET API to retrieve a paginated list of all courses for a given organization,
        along with the specified user's role ("instructor", "staff", or null) in each course.

        Use case:
            - Allows platform admins to audit or review a user's access level across all courses in an organization.
            - Useful for compliance, support, or bulk role management tools.

        Endpoint:
            GET /api/contentstore/v1/course_team/manage?org=<org_code>&email=<user_email>

        Query Parameters:
            org: Organization code (required)
            email: User's email address (required)

        Returns:
            Paginated list of courses for the organization, with the user's role in each course.
            Only accessible by admin users (IsAdminUser permission).

        Example Response:
            {
                "count": 4,
                "next": (
                    "http://example.com/api/contentstore/v1/course_team/manage?email={email}&org={org}"
                    "&page=4&page_size=1"
                ),
                "previous": (
                    "http://example.com/api/contentstore/v1/course_team/manage?email={email}&org={org}"
                    "&page=2&page_size=1"
                ),
                "results": [
                    {
                        "course_id": "course-v1:edX+DemoX+2025_T1",
                        "course_name": "edX Demonstration Course",
                        "role": "instructor"
                    }
                ],
                "current_page": 3,
                "total_pages": 4
            }
        """
        return self.list(request, *args, **kwargs)
