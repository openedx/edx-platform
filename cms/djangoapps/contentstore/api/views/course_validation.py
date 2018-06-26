# pylint: disable=missing-docstring
import logging
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from contentstore.course_info_model import get_course_updates
from contentstore.views.certificates import CertificateManager
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from xmodule.modulestore.django import modulestore

from .utils import get_bool_param, course_author_access_required


log = logging.getLogger(__name__)


@view_auth_classes()
class CourseValidationView(DeveloperErrorViewMixin, GenericAPIView):
    """
    **Use Case**

    **Example Requests**

        GET /api/courses/v1/validation/{course_id}/

    **GET Parameters**

        A GET request may include the following parameters.

        * all
        * dates
        * assignments
        * grades
        * certificates
        * updates
        * graded_only (boolean) - whether to included graded subsections only in the assignments information.

    **GET Response Values**

        The HTTP 200 response has the following values.

        * is_self_paced - whether the course is self-paced.
        * dates
            * has_start_date - whether the start date is set on the course.
            * has_end_date - whether the end date is set on the course.
        * assignments
            * total_number - total number of assignments in the course.
            * total_visible - number of assignments visible to learners in the course.
            * assignments_with_dates_before_start - assignments with due dates before the start date.
            * assignments_with_dates_after_end - assignments with due dates after the end date.
        * grades
            * sum_of_weights - sum of weights for all assignments in the course (valid ones should equal 1).
        * certificates
            * is_activated - whether the certificate is activated for the course.
            * has_certificate - whether the course has a certificate.
        * updates
            * has_update - whether at least one course update exists.

    """
    @course_author_access_required
    def get(self, request, course_key):
        """
        Returns validation information for the given course.
        """
        all_requested = get_bool_param(request, 'all', False)

        store = modulestore()
        with store.bulk_operations(course_key):
            course = store.get_course(course_key, depth=self._required_course_depth(request, all_requested))

            response = dict(
                is_self_paced=course.self_paced,
            )
            if get_bool_param(request, 'dates', all_requested):
                response.update(
                    dates=self._dates_validation(course)
                )
            if get_bool_param(request, 'assignments', all_requested):
                response.update(
                    assignments=self._assignments_validation(course, request)
                )
            if get_bool_param(request, 'grades', all_requested):
                response.update(
                    grades=self._grades_validation(course)
                )
            if get_bool_param(request, 'certificates', all_requested):
                response.update(
                    certificates=self._certificates_validation(course)
                )
            if get_bool_param(request, 'updates', all_requested):
                response.update(
                    updates=self._updates_validation(course, request)
                )

        return Response(response)

    def _required_course_depth(self, request, all_requested):
        if get_bool_param(request, 'assignments', all_requested):
            return 2
        else:
            return 0

    def _dates_validation(self, course):
        return dict(
            has_start_date=self._has_start_date(course),
            has_end_date=course.end is not None,
        )

    def _assignments_validation(self, course, request):
        assignments, visible_assignments = self._get_assignments(course)
        assignments_with_dates = [
            a for a in visible_assignments if a.due
        ]

        assignments_with_dates_before_start = (
            [
                {'id': unicode(a.location), 'display_name': a.display_name}
                for a in assignments_with_dates
                if a.due < course.start
            ]
            if self._has_start_date(course)
            else []
        )

        assignments_with_dates_after_end = (
            [
                {'id': unicode(a.location), 'display_name': a.display_name}
                for a in assignments_with_dates
                if a.due > course.end
            ]
            if course.end
            else []
        )

        if get_bool_param(request, 'graded_only', False):
            assignments_with_dates = [
                a
                for a in visible_assignments
                if a.due and a.graded
            ]

            assignments_with_dates_before_start = [
                {'id': unicode(a.location), 'display_name': a.display_name}
                for a in assignments_with_dates if a.due < course.start
            ]

            assignments_with_dates_after_end = [
                {'id': unicode(a.location), 'display_name': a.display_name}
                for a in assignments_with_dates if a.due > course.end
            ]

        return dict(
            total_number=len(assignments),
            total_visible=len(visible_assignments),
            assignments_with_dates_before_start=assignments_with_dates_before_start,
            assignments_with_dates_after_end=assignments_with_dates_after_end,
        )

    def _grades_validation(self, course):
        sum_of_weights = course.grader.sum_of_weights
        return dict(
            sum_of_weights=sum_of_weights,
        )

    def _certificates_validation(self, course):
        is_activated, certificates = CertificateManager.is_activated(course)
        return dict(
            is_activated=is_activated,
            has_certificate=len(certificates) > 0,
        )

    def _updates_validation(self, course, request):
        updates_usage_key = course.id.make_usage_key('course_info', 'updates')
        updates = get_course_updates(updates_usage_key, provided_id=None, user_id=request.user.id)
        return dict(
            has_update=len(updates) > 0,
        )

    def _get_assignments(self, course):
        store = modulestore()
        sections = [store.get_item(section_usage_key) for section_usage_key in course.children]
        assignments = [
            store.get_item(assignment_usage_key)
            for section in sections
            for assignment_usage_key in section.children
        ]
        visible_sections = [
            s for s in sections
            if not s.visible_to_staff_only and not s.hide_from_toc
        ]
        assignments_in_visible_sections = [
            store.get_item(assignment_usage_key)
            for visible_section in visible_sections
            for assignment_usage_key in visible_section.children
        ]
        visible_assignments = [
            a for a in assignments_in_visible_sections
            if not a.visible_to_staff_only
        ]
        return assignments, visible_assignments

    def _has_start_date(self, course):
        return not course.start_date_is_still_default
