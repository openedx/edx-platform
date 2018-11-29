"""
Defines an endpoint for retrieving assignment type and subsection info for a course.
"""
from contextlib import contextmanager

from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from six import text_type

from openedx.core.djangoapps.util.forms import to_bool
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.core.lib.cache_utils import request_cached
from student.auth import has_course_author_access
from xmodule.modulestore.django import modulestore
from xmodule.util.misc import get_default_short_labeler


@view_auth_classes()
class BaseCourseView(DeveloperErrorViewMixin, GenericAPIView):
    """
    A base class for course info APIs.
    TODO: https://openedx.atlassian.net/browse/EDUCATOR-3755
    This whole thing is duplicated from cms/djangoapps/contentstore
    """
    @contextmanager
    def get_course(self, request, course_key):
        """
        Context manager that yields a course, given a request and course_key.
        """
        store = modulestore()
        with store.bulk_operations(course_key):
            course = store.get_course(course_key, depth=self._required_course_depth(request))
            yield course

    @staticmethod
    def _required_course_depth(request):
        """
        Returns how far deep we need to go into the course tree to
        get all of the information required.  Will use entire tree if the request's
        `all` param is truthy, otherwise goes to depth of 2 (subsections).
        """
        all_requested = get_bool_param(request, 'all', False)
        if all_requested:
            return None
        return 2

    @classmethod
    @request_cached()
    def _get_visible_subsections(cls, course):
        """
        Returns a list of all visible subsections for a course.
        """
        _, visible_sections = cls._get_sections(course)
        visible_subsections = []
        for section in visible_sections:
            visible_subsections.extend(cls._get_visible_children(section))
        return visible_subsections

    @classmethod
    @request_cached()
    def _get_sections(cls, course):
        """
        Returns all sections in the course.
        """
        return cls._get_all_children(course)

    @classmethod
    def _get_all_children(cls, parent):
        """
        Returns all child nodes of the given parent.
        """
        store = modulestore()
        children = [store.get_item(child_usage_key) for child_usage_key in cls._get_children(parent)]
        visible_children = [
            c for c in children
            if not c.visible_to_staff_only and not c.hide_from_toc
        ]
        return children, visible_children

    @classmethod
    def _get_visible_children(cls, parent):
        """
        Returns only the visible children of the given parent.
        """
        _, visible_chidren = cls._get_all_children(parent)
        return visible_chidren

    @classmethod
    def _get_children(cls, parent):
        """
        Returns the value of the 'children' attribute of a node.
        """
        if not hasattr(parent, 'children'):
            return []
        else:
            return parent.children


def get_bool_param(request, param_name, default):
    """
    Given a request, parameter name, and default value, returns
    either a boolean value or the default.
    """
    param_value = request.query_params.get(param_name, None)
    bool_value = to_bool(param_value)
    if bool_value is None:
        return default
    else:
        return bool_value


def course_author_access_required(view):
    """
    Ensure the user making the API request has course author access to the given course.

    This decorator parses the course_id parameter, checks course access, and passes
    the parsed course_key to the view as a parameter. It will raise a
    403 error if the user does not have author access.

    Usage::
        @course_author_access_required
        def my_view(request, course_key):
            # Some functionality ...
    """
    def _wrapper_view(self, request, course_id, *args, **kwargs):
        """
        Checks for course author access for the given course by the requesting user.
        Calls the view function if has access, otherwise raises a 403.
        """
        course_key = CourseKey.from_string(course_id)
        if not has_course_author_access(request.user, course_key):
            raise DeveloperErrorViewMixin.api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='The requesting user does not have course author permissions.',
                error_code='user_permissions',
            )
        return view(self, request, course_key, *args, **kwargs)
    return _wrapper_view


class CourseGradingView(BaseCourseView):
    """
    Returns information about assignments and assignment types for a course.
    **Example Requests**

        GET /api/grades/v1/gradebook/{course_id}/grading-info

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
