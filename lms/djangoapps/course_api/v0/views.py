""" API implementation for course-oriented interactions. """

import logging

from django.core.urlresolvers import reverse
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework import generics
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api.views import APIViewWithPermissions, PaginatedListAPIViewWithPermissions, PermissionMixin

from courseware.courses import course_image_url
from course_api.courseware_access import get_course, get_course_child, get_course_descriptor
from course_api.v0.serializers import CourseSerializer, GradedContentSerializer, GradingPolicySerializer


log = logging.getLogger(__name__)


def _serialize_content(request, course_key, content_descriptor):
    """
    Loads the specified content object into the response dict
    This should probably evolve to use DRF serializers
    """

    data = {}

    if hasattr(content_descriptor, 'display_name'):
        data['name'] = content_descriptor.display_name

    if hasattr(content_descriptor, 'due'):
        data['due'] = content_descriptor.due

    data['start'] = getattr(content_descriptor, 'start', None)
    data['end'] = getattr(content_descriptor, 'end', None)

    data['category'] = content_descriptor.location.category

    # Some things we only do if the content object is a course
    if content_descriptor.scope_ids.block_type == 'course':
        content_id = unicode(content_descriptor.id)
        content_uri = request.build_absolute_uri(reverse('course_api:v0:detail', kwargs={'course_id': content_id}))
        data['course'] = content_descriptor.location.course
        data['org'] = content_descriptor.location.org
        data['run'] = content_descriptor.location.run

    # Other things we do only if the content object is not a course
    else:
        content_id = unicode(content_descriptor.location)
        # Need to use the CourseKey here, which will possibly result in a different (but valid)
        # URI due to the change in key formats during the "opaque keys" transition
        content_uri = request.build_absolute_uri(reverse('course_api:v0:content:detail',
                                                         kwargs={'course_id': unicode(course_key),
                                                                 'content_id': content_id}))

    data['id'] = unicode(content_id)
    data['uri'] = content_uri

    # Include any additional fields requested by the caller
    include_fields = request.QUERY_PARAMS.get('include_fields', None)
    if include_fields:
        include_fields = include_fields.split(',')
        for field in include_fields:
            data[field] = getattr(content_descriptor, field, None)

    return data


def _serialize_content_with_children(request, course_key, descriptor, depth):  # pylint: disable=invalid-name
    """
    Serializes course content and then dives into the content tree,
    serializing each child module until specified depth limit is hit
    """
    data = _serialize_content(
        request,
        course_key,
        descriptor
    )

    if depth > 0:
        data['children'] = []
        for child in descriptor.get_children():
            data['children'].append(_serialize_content_with_children(request, course_key, child, depth - 1))
    return data


def _get_course_data(request, course_key, course_descriptor, depth=0):
    """
    creates a dict of course attributes
    """

    if depth > 0:
        data = _serialize_content_with_children(
            request,
            course_key,
            course_descriptor,  # Primer for recursive function
            depth
        )
        data['content'] = data['children']
        data.pop('children')
    else:
        data = _serialize_content(
            request,
            course_key,
            course_descriptor
        )

    data['image_url'] = ''
    if getattr(course_descriptor, 'course_image'):
        data['image_url'] = course_image_url(course_descriptor)

    return data


class DepthMixin(object):
    # TODO Test this!
    def get_depth(self, request, default=0):
        try:
            return int(request.QUERY_PARAMS.get('depth', default))
        except ValueError:
            raise ParseError


class CourseContentList(DepthMixin, APIViewWithPermissions):
    """
    **Use Case**

        CourseContentList gets a collection of content for a given
        course. You can use the **uri** value in
        the response to get details for that content entity.

        The optional **depth** parameter that allows clients to get child content down to the specified tree level.

    **Example requests**:

        GET /api/courses/v0/{course_id}/content/

        GET /api/courses/v0/{course_id}/content/

    **Response Values**

        * category: The type of content.

        * due: The due date.

        * uri: The URI to use to get details of the content entity.

        * id: The unique identifier for the content entity.

        * name: The name of the course.
    """

    def get(self, request, course_id):
        """
        GET /api/courses/v0/{course_id}/content/
        """
        depth = self.get_depth(request, 1)
        course_descriptor, course_key, _course_content = get_course(course_id, depth=depth)

        if not course_descriptor:
            raise Http404

        response_data = [
            _serialize_content_with_children(request, course_key, child, depth - 1)
            for child in course_descriptor.get_children()
        ]

        return Response(response_data)


class CourseContentDetail(DepthMixin, APIViewWithPermissions):
    """
    **Use Case**

        CourseContentDetail returns a JSON collection for a specified
        CourseContent entity. If the specified CourseContent is the Course, the
        course representation is returned. You can use the uri values in the
        children collection in the JSON response to get details for that content
        entity.

        The optional **depth** parameter that allows clients to get child content down to the specified tree level.

    **Example Request**

          GET /api/courses/v0/{course_id}/content/{content_id}/

    **Response Values**

        * category: The type of content.

        * name: The name of the content entity.

        * due:  The due date.

        * uri: The URI of the content entity.

        * id: The unique identifier for the course.

        * children: Content entities that this content entity contains.
    """

    def get(self, request, course_id, content_id):
        """
        GET /api/courses/v0/{course_id}/content/{content_id}/
        """
        depth = self.get_depth(request)

        # Verify the course exists.
        course_descriptor, course_key, _course_content = get_course(course_id)
        if not course_descriptor:
            raise Http404

        content_descriptor, _content_key, _content = get_course_child(request, request.user, course_key, content_id)

        # TODO Add category filtering
        response_data = _serialize_content_with_children(request, course_key, content_descriptor, depth)
        return Response(response_data, status=status.HTTP_200_OK)


class CourseList(PaginatedListAPIViewWithPermissions):
    """
    **Use Case**

        CourseList returns paginated list of courses in the edX Platform. The list can be
        filtered by course_id

    **Example Request**

          GET /api/courses/v0/
          GET /api/courses/v0/?course_id={course_id1},{course_id2}

    **Response Values**

        * category: The type of content. In this case, the value is always "course".

        * name: The name of the course.

        * uri: The URI to use to get details of the course.

        * course: The course number.

        * due:  The due date. For courses, the value is always null.

        * org: The organization specified for the course.

        * id: The unique identifier for the course.
    """
    serializer_class = CourseSerializer

    def get_queryset(self):
        course_ids = self.request.QUERY_PARAMS.get('course_id', None)

        course_descriptors = []
        if course_ids:
            course_ids = course_ids.split(',')
            for course_id in course_ids:
                course_key = CourseKey.from_string(course_id)
                course_descriptor = get_course_descriptor(course_key, 0)
                course_descriptors.append(course_descriptor)
        else:
            course_descriptors = modulestore().get_courses()

        results = [
            _get_course_data(self.request, descriptor.id, descriptor)
            for descriptor in course_descriptors
        ]

        # Sort the results in a predictable manner.
        results.sort(key=lambda x: x['id'])

        return results


class CourseDetail(DepthMixin, APIViewWithPermissions):
    """
    **Use Case**

        CourseDetail returns details for a course.

        The optional **depth** parameter that allows clients to get child content down to the specified tree level.

    **Example requests**:

        GET /api/courses/v0/{course_id}/

        GET /api/courses/v0/{course_id}/?depth=2

    **Response Values**

        * category: The type of content.

        * name: The name of the course.

        * uri: The URI to use to get details of the course.

        * course: The course number.

        * content: When the depth parameter is used, a collection of child
          course content entities, such as chapters, sequentials, and
          components.

        * due:  The due date. For courses, the value is always null.

        * org: The organization specified for the course.

        * id: The unique identifier for the course.
    """

    def get(self, request, course_id):
        """
        GET /api/courses/v0/{course_id}/
        """
        depth = self.get_depth(request)
        # get_course_by_id raises an Http404 if the requested course is invalid
        # Rather than catching it, we just let it bubble up
        course_descriptor, course_key, _course_content = get_course(course_id, depth=depth)
        if not course_descriptor:
            raise Http404
        response_data = _get_course_data(request, course_key, course_descriptor, depth)
        return Response(response_data, status=status.HTTP_200_OK)


class CourseGradedContent(PermissionMixin, generics.ListAPIView):
    """
    **Use Case**

        Retrieves course graded content and problems.

    **Example requests**:

        GET /api/courses/v0/{course_id}/graded_content/

    **Response Values**

        * id: The ID of the content.

        * name: The name of the content.

        * format: The type of the content (e.g. Exam, Homework). Note: These values are course-dependent.
          Do not make any assumptions based on assignment type.

        * problems: {
            * id: The ID of the problem.

            * name: The name of the problem.
        }
    """

    serializer_class = GradedContentSerializer
    allow_empty = False

    def _filter_problems(self, node):
        """ Retrieve the problems from the node/tree. """

        if node.category == u'problem':
            return [node]

        if not node.has_children:
            return []

        problems = []
        for child in node.get_children():
            problems += self._filter_problems(child)

        return problems

    def get_course_graded_content(self, course_key):
        """
        Retrieve course graded (e.g. homework, exams) from the module store.
        """
        _modulestore = modulestore()

        # Ensure the course exists
        if not _modulestore.get_course(course_key):
            raise Http404

        items = _modulestore.get_items(course_key, settings={'graded': True})

        for item in items:
            problems = self._filter_problems(item)
            item.problems = problems

        return items

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        course_key = CourseKey.from_string(course_id)
        return self.get_course_graded_content(course_key)


class CourseGradingPolicy(PermissionMixin, generics.ListAPIView):
    """
    **Use Case**

        Retrieves course grading policy.

    **Example requests**:

        GET /api/courses/v0/{course_id}/grading_policy/

    **Response Values**

        * assignment_type: The type of the assignment (e.g. Exam, Homework). Note: These values are course-dependent.
          Do not make any assumptions based on assignment type.

        * count: Number of assignments of the type.

        * dropped: Number of assignments of the type that are dropped.

        * weight: Effect of the assignment type on grading.
    """

    serializer_class = GradingPolicySerializer
    allow_empty = False

    def get_grading_policy(self, course_key):
        """
        Retrieve course grading policy from the module store.
        """
        course = modulestore().get_course(course_key)

        # Ensure the course exists
        if not course:
            raise Http404

        # Return the raw data. The serializer will handle the field mappings.
        return course.raw_grader

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        course_key = CourseKey.from_string(course_id)
        return self.get_grading_policy(course_key)
