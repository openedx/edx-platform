"""
REST API views for course cohorts, v2.

Consolidates the three v1 function-and-APIView surfaces (cohort list/detail,
cohort membership and course cohort settings) into DRF ViewSets registered
through a router.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.course_groups import api as cohort_api
from openedx.core.djangoapps.course_groups import cohorts
from openedx.core.djangoapps.course_groups.models import (
    CohortMembership,
    CourseUserGroup,
    CourseUserGroupPartitionGroup,
)
from openedx.core.djangoapps.course_groups.rest_api.cohort_permissions import CanManageCohorts
from openedx.core.djangoapps.course_groups.rest_api.cohort_serializers import (
    CohortMembershipRequestSerializer,
    CohortMemberSerializer,
    CohortSerializer,
    CohortSettingsSerializer,
    CohortUpdateSerializer,
    represent_cohort,
)
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin

User = get_user_model()


class CohortAPIAccessMixin:
    """
    Authentication and authorization shared by every v2 cohort endpoint.

    JWT is the standard scheme for user-authenticated requests. Session
    authentication keeps the Studio and instructor dashboard front ends
    working, and the inactive-user variant is retained deliberately: the v1
    surface accepted inactive users over session, and narrowing that here
    would lock out callers that work today.

    Authorization lives entirely in the permission class. The handlers do not
    repeat it, which is what the v1 views did by calling get_course_with_access
    again inside each method.
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated, CanManageCohorts)

    def initial(self, request, *args, **kwargs):
        """
        Reject a malformed course key before the permission check runs.

        The key is validated for syntax only. Whether the course exists is
        checked inside the handlers, after authorization, so that a 404 cannot
        be used to probe for courses.
        """
        course_key_string = kwargs.get("course_key_string")
        if course_key_string is not None:
            try:
                CourseKey.from_string(course_key_string)
            except InvalidKeyError as exc:
                raise self.api_error(
                    status.HTTP_404_NOT_FOUND,
                    f"{course_key_string} is not a valid course key.",
                    "invalid-course-key",
                ) from exc
        super().initial(request, *args, **kwargs)


class CourseScopedMixin:
    """
    Resolves the course key that every cohort resource is addressed under.
    """

    @property
    def course_key(self):
        """Return the course key taken from the request path."""
        return CourseKey.from_string(self.kwargs["course_key_string"])

    def get_cohort_or_404(self):
        """Return the cohort named in the path, or raise a 404."""
        try:
            return cohorts.get_cohort_by_id(self.course_key, self.kwargs["cohort_id"])
        except CourseUserGroup.DoesNotExist as exc:
            raise self.api_error(
                status.HTTP_404_NOT_FOUND,
                f"No cohort {self.kwargs['cohort_id']} in {self.kwargs['course_key_string']}.",
                "cohort-not-found",
            ) from exc


class CohortViewSet(CohortAPIAccessMixin, CourseScopedMixin, DeveloperErrorViewMixin, viewsets.ViewSet):
    """
    List, create, read and update the cohorts of a course.
    """

    serializer_class = CohortSerializer
    lookup_url_kwarg = "cohort_id"

    def list(self, request, course_key_string):
        """Return the cohorts of this course."""
        course_key = self.course_key
        records = cohorts.get_course_cohorts(course_id=course_key)
        return Response([represent_cohort(c, course_key) for c in records])

    def retrieve(self, request, course_key_string, cohort_id):
        """Return a single cohort."""
        cohort = self.get_cohort_or_404()
        return Response(represent_cohort(cohort, self.course_key))

    def create(self, request, course_key_string):
        """Create a cohort in this course."""
        serializer = CohortSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        course_key = self.course_key

        if cohorts.is_cohort_exists(course_key, data["name"]):
            raise self.api_error(
                status.HTTP_400_BAD_REQUEST,
                "A cohort with that name already exists in this course.",
                "cohort-name-exists",
            )

        cohort = cohorts.add_cohort(course_key, data["name"], data["assignment_type"])
        if data.get("group_id") is not None or data.get("user_partition_id") is not None:
            self._apply_content_group(cohort, data)
        return Response(represent_cohort(cohort, course_key), status=status.HTTP_201_CREATED)

    def partial_update(self, request, course_key_string, cohort_id):
        """Update a cohort's name, assignment type or content group."""
        serializer = CohortUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        course_key = self.course_key
        cohort = self.get_cohort_or_404()

        name = data.get("name")
        if name is not None and name != cohort.name:
            if cohorts.is_cohort_exists(course_key, name):
                raise self.api_error(
                    status.HTTP_400_BAD_REQUEST,
                    "A cohort with that name already exists in this course.",
                    "cohort-name-exists",
                )
            cohort.name = name
            cohort.save()

        if data.get("assignment_type") is not None:
            try:
                cohorts.set_assignment_type(cohort, data["assignment_type"])
            except ValueError as exc:
                raise self.api_error(
                    status.HTTP_400_BAD_REQUEST, str(exc), "last-random-cohort"
                ) from exc

        if "group_id" in request.data:
            self._apply_content_group(cohort, data)

        return Response(represent_cohort(cohort, course_key))

    def _apply_content_group(self, cohort, data):
        """
        Link or unlink the cohort's content group association.

        A ``group_id`` of None unlinks any existing association, which is
        distinct from the caller omitting the field entirely.
        """
        group_id = data.get("group_id")
        partition_id = data.get("user_partition_id")
        existing_group_id, existing_partition_id = cohorts.get_group_info_for_cohort(cohort)

        if group_id is None:
            if existing_group_id is not None:
                CourseUserGroupPartitionGroup.objects.filter(course_user_group=cohort).delete()
            return

        if partition_id is None:
            raise self.api_error(
                status.HTTP_400_BAD_REQUEST,
                "user_partition_id is required when group_id is supplied.",
                "missing-user-partition-id",
            )
        if group_id != existing_group_id or partition_id != existing_partition_id:
            CourseUserGroupPartitionGroup.objects.filter(course_user_group=cohort).delete()
            CourseUserGroupPartitionGroup(
                course_user_group=cohort,
                partition_id=partition_id,
                group_id=group_id,
            ).save()


class CohortMemberViewSet(CohortAPIAccessMixin, CourseScopedMixin, DeveloperErrorViewMixin, viewsets.ViewSet):
    """
    List the learners in a cohort, add learners to it and remove one from it.
    """

    serializer_class = CohortMemberSerializer
    lookup_url_kwarg = "username"
    lookup_value_regex = r"[\w.@+-]+"

    def list(self, request, course_key_string, cohort_id):
        """Return the learners in this cohort."""
        cohort = self.get_cohort_or_404()
        return Response(CohortMemberSerializer(cohort.users.all(), many=True).data)

    def create(self, request, course_key_string, cohort_id):
        """Add the named learners to this cohort."""
        cohort = self.get_cohort_or_404()
        serializer = CohortMembershipRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = {key: [] for key in
                  ("added", "changed", "present", "unknown", "preassigned", "invalid")}
        for identifier in serializer.validated_data["users"]:
            try:
                user, previous_cohort, preassigned = cohorts.add_user_to_cohort(cohort, identifier)
            except User.DoesNotExist:
                result["unknown"].append(identifier)
            except DjangoValidationError:
                result["invalid"].append(identifier)
            except ValueError:
                result["present"].append(identifier)
            else:
                if preassigned:
                    result["preassigned"].append(identifier)
                elif previous_cohort:
                    result["changed"].append({
                        "username": user.username,
                        "email": user.email,
                        "previous_cohort": previous_cohort,
                    })
                else:
                    result["added"].append({"username": user.username, "email": user.email})
        return Response(result)

    def destroy(self, request, course_key_string, cohort_id, username):
        """Remove one learner from this cohort."""
        cohort = self.get_cohort_or_404()
        try:
            cohort_api.remove_user_from_cohort(self.course_key, username, cohort.id)
        except User.DoesNotExist as exc:
            raise self.api_error(
                status.HTTP_404_NOT_FOUND, f"No user named {username}.", "user-not-found"
            ) from exc
        except CohortMembership.DoesNotExist as exc:
            raise self.api_error(
                status.HTTP_400_BAD_REQUEST,
                f"{username} is not a member of this cohort.",
                "user-not-in-cohort",
            ) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class CohortSettingsView(CohortAPIAccessMixin, DeveloperErrorViewMixin, APIView):
    """
    Read and update whether a course uses cohorts.
    """

    serializer_class = CohortSettingsSerializer

    def get(self, request, course_key_string):
        """Return the course's cohort configuration."""
        course_key = CourseKey.from_string(course_key_string)
        return Response(self._representation(course_key))

    def put(self, request, course_key_string):
        """Enable or disable cohorts for the course."""
        course_key = CourseKey.from_string(course_key_string)
        serializer = CohortSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cohorts.set_course_cohorted(course_key, serializer.validated_data["is_cohorted"])
        except ValueError as exc:
            raise self.api_error(
                status.HTTP_400_BAD_REQUEST, str(exc), "invalid-cohort-setting"
            ) from exc
        return Response(self._representation(course_key))

    @staticmethod
    def _representation(course_key):
        """Build the cohort settings payload for a course."""
        return {
            "id": cohorts.get_course_cohort_id(course_key),
            "is_cohorted": cohorts.is_course_cohorted(course_key),
        }
