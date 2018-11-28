"""
Defines an endpoint for retrieving assignment type and subsection info for a course.
"""
from rest_framework.response import Response
from six import text_type

from xmodule.util.misc import get_default_short_labeler

from .utils import BaseCourseView, course_author_access_required, get_bool_param


class CourseGradingView(BaseCourseView):
    """
    Returns information about assignments and assignment types for a course.
    **Example Requests**

        GET /api/courses/v1/grading/{course_id}/

    **GET Parameters**

        A GET request may include the following parameters.

        * graded_only (boolean) - If true, only returns subsection data for graded subsections (defaults to False).

    **GET Response Values**

        The HTTP 200 response has the following values.

        * assignment_types - A dictionary keyed by the assignment type name with the following values:
            * min_count - The minimum number of required assignments of this type.
            * weight - The weight assigned to this assignment type for course grading.
            * type - The name of the assignment type.
            * drop_count - The maximum number of assignments of this type that can be dropped.
            * short_label - The short label prefix used for short labels of assignments of this type (e.g. 'HW').

        * subsections - A list of subsections contained in this course.
            * module_id - The string version of this subsection's location.
            * display_name - The display name of this subsection.
            * graded - Boolean indicating whether this subsection is graded (for at least one user in the course).
            * short_label - A short label for graded assignments (e.g. 'HW 01').
            * assignment_type - The assignment type of this subsection (for graded assignments only).

    """
    @course_author_access_required
    def get(self, request, course_key):
        """
        Returns grading information (which subsections are graded, assignment types) for
        the requested course.
        """
        graded_only = get_bool_param(request, 'graded_only', False)

        with self.get_course(request, course_key) as course:
            results = {
                'assignment_types': self._get_assignment_types(course),
                'subsections': self._get_subsections(course, graded_only),
            }
            return Response(results)

    def _get_assignment_types(self, course):
        """
        Helper function that returns a serialized dict of assignment types
        for the given course.
        Args:
            course - A course object.
        """
        serialized_grading_policies = {}
        for grader, assignment_type, weight in course.grader.subgraders:
            serialized_grading_policies[assignment_type] = {
                'type': assignment_type,
                'short_label': grader.short_label,
                'min_count': grader.min_count,
                'drop_count': grader.drop_count,
                'weight': weight,
            }
        return serialized_grading_policies

    def _get_subsections(self, course, graded_only=False):
        """
        Helper function that returns a list of subsections contained in the given course.
        Args:
            course - A course object.
            graded_only - If true, returns only graded subsections (defaults to False).
        """
        subsections = []
        short_labeler = get_default_short_labeler(course)
        for subsection in self._get_visible_subsections(course):
            if graded_only and not subsection.graded:
                continue

            short_label = None
            if subsection.graded:
                short_label = short_labeler(subsection.format)

            subsections.append({
                'assignment_type': subsection.format,
                'graded': subsection.graded,
                'short_label': short_label,
                'module_id': text_type(subsection.location),
                'display_name': subsection.display_name,
            })
        return subsections
