"""
API views for course dates.
"""

from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db.models import Case, F, OuterRef, Q, Subquery, When, BooleanField
from django.shortcuts import get_object_or_404
from django.utils import timezone
from edx_when.models import ContentDate
from rest_framework import mixins, viewsets
from rest_framework.pagination import PageNumberPagination

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from ..decorators import mobile_view
from .serializers import ContentDateSerializer


class AllCourseDatesPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


@mobile_view()
class AllCourseDatesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for retrieving all course dates for a specific user.
    This viewset provides a list of course dates for a user, including due dates for
    assignments and other course content.

    **Example Request**

        GET /api/mobile/{api_version}/course_dates/<user_name>/

    **Example Response**

        ```json
        {
            "count": 2,
            "next": null,
            "previous": null,
            "results": [
            {
                "course_id": "course-v1:1+1+1",
                "assignment_block_id": "block-v1:1+1+1+type@sequential+block@bafd854414124f6db42fee42ca8acc14",
                "due_date": "2025-02-28 00:00:00+00:00",
                "assignment_title": "Subsection name",
                "learner_has_access": true,
                "course_name": "Course name",
                "relative": false
            },
            {
                "course_id": "course-v1:1+1+1",
                "assignment_block_id": "block-v1:1+1+1+type@sequential+block@bf9f2d55cf4f49eaa71e7157ea67ba32",
                "due_date": "2025-03-03 00:30:00+00:00",
                "assignment_title": "Subsection name",
                "learner_has_access": true,
                "course_name": "Course name",
                "relative": true
            },
        }
        ```

    """

    pagination_class = AllCourseDatesPagination
    serializer_class = ContentDateSerializer

    def get_queryset(self):
        """
        Returns a queryset of ContentDate objects filtered and annotated based on the user's course enrollments.
        The queryset is filtered to include only content dates for courses the user is enrolled in,
        and further filtered to exclude past due dates for non-self-paced courses and content dates
        without a relative date policy.

        The resulting queryset is ordered by the due date.

        Returns:
            QuerySet: A queryset of ContentDate objects.
        """

        user = get_object_or_404(User, username=self.kwargs.get("username"))
        user_enrollments = CourseEnrollment.enrollments_for_user(user).select_related("course")
        course_ids = user_enrollments.values_list("course_id", flat=True)
        not_self_paced_course_ids = user_enrollments.filter(course__self_paced=False).values_list(
            "course_id", flat=True
        )

        enrollment_created_subquery = Subquery(
            CourseEnrollment.objects.filter(user=user, course_id=OuterRef("course_id")).values("created")[:1]
        )
        course_name_subquery = Subquery(
            CourseOverview.objects.filter(id=OuterRef("course_id")).values("display_name")[:1]
        )

        return (
            ContentDate.objects.filter(active=True, course_id__in=course_ids, field="due")
            .annotate(
                course_name=course_name_subquery,
                enrollment_created=enrollment_created_subquery,
                due_date=Case(
                    When(
                        policy__rel_date__isnull=False,
                        then=F("enrollment_created") + F("policy__rel_date"),
                    ),
                    default=F("policy__abs_date"),
                ),
                relative=Case(
                    When(policy__rel_date__isnull=False, then=True),
                    default=False,
                    output_field=BooleanField(),
                ),
            )
            .exclude(
                Q(due_date__lt=timezone.now(), course_id__in=not_self_paced_course_ids)
                | Q(due_date__lt=timezone.now(), policy__rel_date__isnull=True)
            )
            .order_by("due_date")
        )
