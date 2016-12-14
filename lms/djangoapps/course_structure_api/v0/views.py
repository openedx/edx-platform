""" API implementation for course-oriented interactions. """

from collections import namedtuple
import json
import logging

from django.conf import settings
from django.http import Http404
from rest_framework.authentication import SessionAuthentication
from rest_framework_oauth.authentication import OAuth2Authentication
from rest_framework.exceptions import AuthenticationFailed, ParseError
from rest_framework.generics import RetrieveAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey

from course_structure_api.v0 import serializers
from courseware import courses
from courseware.access import has_access
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from openedx.core.lib.api.view_utils import view_course_access, view_auth_classes
from openedx.core.djangoapps.content.course_structures.api.v0 import api, errors
from openedx.core.lib.exceptions import CourseNotFoundError
from student.roles import CourseInstructorRole, CourseStaffRole
from util.module_utils import get_dynamic_descriptor_children


log = logging.getLogger(__name__)


class CourseViewMixin(object):
    """
    Mixin for views dealing with course content. Also handles authorization and authentication.
    """
    lookup_field = 'course_id'
    authentication_classes = (OAuth2Authentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_course_or_404(self):
        """
        Retrieves the specified course, or raises an Http404 error if it does not exist.
        Also checks to ensure the user has permissions to view the course
        """
        try:
            course_id = self.kwargs.get('course_id')
            course_key = CourseKey.from_string(course_id)
            course = courses.get_course(course_key)
            self.check_course_permissions(self.request.user, course_key)

            return course
        except ValueError:
            raise Http404

    @staticmethod
    def course_check(func):
        """Decorator responsible for catching errors finding and returning a 404 if the user does not have access
        to the API function.

        :param func: function to be wrapped
        :returns: the wrapped function
        """
        def func_wrapper(self, *args, **kwargs):
            """Wrapper function for this decorator.

            :param *args: the arguments passed into the function
            :param **kwargs: the keyword arguments passed into the function
            :returns: the result of the wrapped function
            """
            try:
                course_id = self.kwargs.get('course_id')
                self.course_key = CourseKey.from_string(course_id)
                self.check_course_permissions(self.request.user, self.course_key)
                return func(self, *args, **kwargs)
            except CourseNotFoundError:
                raise Http404

        return func_wrapper

    def user_can_access_course(self, user, course):
        """
        Determines if the user is staff or an instructor for the course.
        Always returns True if DEBUG mode is enabled.
        """
        return bool(
            settings.DEBUG
            or has_access(user, CourseStaffRole.ROLE, course)
            or has_access(user, CourseInstructorRole.ROLE, course)
        )

    def check_course_permissions(self, user, course):
        """
        Checks if the request user can access the course.
        Raises 404 if the user does not have course access.
        """
        if not self.user_can_access_course(user, course):
            raise Http404

    def perform_authentication(self, request):
        """
        Ensures that the user is authenticated (e.g. not an AnonymousUser), unless DEBUG mode is enabled.
        """
        super(CourseViewMixin, self).perform_authentication(request)
        if request.user.is_anonymous() and not settings.DEBUG:
            raise AuthenticationFailed


class CourseList(CourseViewMixin, ListAPIView):
    """
    **Use Case**

        Get a paginated list of courses in the edX Platform.

        The list can be filtered by course_id.

        Each page in the list can contain up to 10 courses.

    **Example Requests**

          GET /api/course_structure/v0/courses/

          GET /api/course_structure/v0/courses/?course_id={course_id1},{course_id2}

    **Response Values**

        * count: The number of courses in the edX platform.

        * next: The URI to the next page of courses.

        * previous: The URI to the previous page of courses.

        * num_pages: The number of pages listing courses.

        * results:  A list of courses returned. Each collection in the list
          contains these fields.

            * id: The unique identifier for the course.

            * name: The name of the course.

            * category: The type of content. In this case, the value is always
              "course".

            * org: The organization specified for the course.

            * run: The run of the course.

            * course: The course number.

            * uri: The URI to use to get details of the course.

            * image_url: The URI for the course's main image.

            * start: The course start date.

            * end: The course end date. If course end date is not specified, the
              value is null.
    """
    serializer_class = serializers.CourseSerializer

    def get_queryset(self):
        course_ids = self.request.query_params.get('course_id', None)

        results = []
        if course_ids:
            course_ids = course_ids.split(',')
            for course_id in course_ids:
                course_key = CourseKey.from_string(course_id)
                course_descriptor = courses.get_course(course_key)
                results.append(course_descriptor)
        else:
            results = modulestore().get_courses()

        # Ensure only course descriptors are returned.
        results = (course for course in results if course.scope_ids.block_type == 'course')

        # Ensure only courses accessible by the user are returned.
        results = (course for course in results if self.user_can_access_course(self.request.user, course))

        # Sort the results in a predictable manner.
        return sorted(results, key=lambda course: unicode(course.id))


class CourseDetail(CourseViewMixin, RetrieveAPIView):
    """
    **Use Case**

        Get details for a specific course.

    **Example Request**:

        GET /api/course_structure/v0/courses/{course_id}/

    **Response Values**

        * id: The unique identifier for the course.

        * name: The name of the course.

        * category: The type of content.

        * org: The organization that is offering the course.

        * run: The run of the course.

        * course: The course number.

        * uri: The URI to use to get details about the course.

        * image_url: The URI for the course's main image.

        * start: The course start date.

        * end: The course end date. If course end date is not specified, the
          value is null.
    """
    serializer_class = serializers.CourseSerializer

    def get_object(self, queryset=None):
        return self.get_course_or_404()


class CourseStructure(CourseViewMixin, RetrieveAPIView):
    """
    **Use Case**

        Get the course structure. This endpoint returns all blocks in the
        course.

    **Example requests**:

        GET /api/course_structure/v0/course_structures/{course_id}/

    **Response Values**

        * root: The ID of the root node of the course structure.

        * blocks: A dictionary that maps block IDs to a collection of
          information about each block. Each block contains the following
          fields.

          * id: The ID of the block.

          * type: The type of block. Possible values include sequential,
            vertical, html, problem, video, and discussion. The type can also be
            the name of a custom type of block used for the course.

          * display_name: The display name configured for the block.

          * graded: Whether or not the sequential or problem is graded. The
            value is true or false.

          * format: The assignment type.

          * children: If the block has child blocks, a list of IDs of the child
            blocks in the order they appear in the course.
    """

    @CourseViewMixin.course_check
    def get(self, request, **kwargs):
        try:
            return Response(api.course_structure(self.course_key))
        except errors.CourseStructureNotAvailableError:
            # If we don't have data stored, we will try to regenerate it, so
            # return a 503 and as them to retry in 2 minutes.
            return Response(status=503, headers={'Retry-After': '120'})


class CourseGradingPolicy(CourseViewMixin, ListAPIView):
    """
    **Use Case**

        Get the course grading policy.

    **Example requests**:

        GET /api/course_structure/v0/grading_policies/{course_id}/

    **Response Values**

        * assignment_type: The type of the assignment, as configured by course
          staff. For example, course staff might make the assignment types Homework,
          Quiz, and Exam.

        * count: The number of assignments of the type.

        * dropped: Number of assignments of the type that are dropped.

        * weight: The weight, or effect, of the assignment type on the learner's
          final grade.
    """

    allow_empty = False

    @CourseViewMixin.course_check
    def get(self, request, **kwargs):
        return Response(api.course_grading_policy(self.course_key))


@view_auth_classes()
class CourseBlocksAndNavigation(ListAPIView):
    """
    **Use Case**

        The following endpoints return the content of the course according to the requesting user's access level.

        * Blocks - Get the course's blocks.

        * Navigation - Get the course's navigation information per the navigation depth requested.

        * Blocks+Navigation - Get both the course's blocks and the course's navigation information.

    **Example requests**:

        GET api/course_structure/v0/courses/{course_id}/blocks/
        GET api/course_structure/v0/courses/{course_id}/navigation/
        GET api/course_structure/v0/courses/{course_id}/blocks+navigation/
           &block_count=video
           &block_json={"video":{"profiles":["mobile_low"]}}
           &fields=graded,format,multi_device

    **Parameters**:

        * block_json: (dict) Indicates for which block types to return student_view_json data.  The key is the block
          type and the value is the "context" that is passed to the block's student_view_json method.

          Example: block_json={"video":{"profiles":["mobile_high","mobile_low"]}}

        * block_count: (list) Indicates for which block types to return the aggregate count of the blocks.

          Example: block_count="video,problem"

        * fields: (list) Indicates which additional fields to return for each block.
          Default is "children,graded,format,multi_device"

          Example: fields=graded,format,multi_device

        * navigation_depth (integer) Indicates how far deep to traverse into the course hierarchy before bundling
          all the descendants.
          Default is 3 since typical navigational views of the course show a maximum of chapter->sequential->vertical.

          Example: navigation_depth=3

    **Response Values**

        The following fields are returned with a successful response.
        Only either one of blocks, navigation, or blocks+navigation is returned depending on which endpoint is used.
        The "root" field is returned for all endpoints.

        * root: The ID of the root node of the course blocks.

        * blocks: A dictionary that maps block usage IDs to a collection of information about each block.
          Each block contains the following fields.  Returned only if using the "blocks" endpoint.

          * id: (string) The usage ID of the block.

          * type: (string) The type of block. Possible values include course, chapter, sequential, vertical, html,
            problem, video, and discussion. The type can also be the name of a custom type of block used for the course.

          * display_name: (string) The display name of the block.

          * children: (list) If the block has child blocks, a list of IDs of the child blocks.
            Returned only if the "children" input parameter is True.

          * block_count: (dict) For each block type specified in the block_count parameter to the endpoint, the
            aggregate number of blocks of that type for this block and all of its descendants.
            Returned only if the "block_count" input parameter contains this block's type.

          * block_json: (dict) The JSON data for this block.
            Returned only if the "block_json" input parameter contains this block's type.

          * block_url: (string) The URL to retrieve the HTML rendering of this block.  The HTML could include
            CSS and Javascript code.  This URL can be used as a fallback if the custom block_json for this
            block type is not requested and not supported.

          * web_url: (string) The URL to the website location of this block.  This URL can be used as a further
            fallback if the block_url and the block_json is not supported.

          * graded (boolean) Whether or not the block or any of its descendants is graded.
            Returned only if "graded" is included in the "fields" parameter.

          * format: (string) The assignment type of the block.
            Possible values can be "Homework", "Lab", "Midterm Exam", and "Final Exam".
            Returned only if "format" is included in the "fields" parameter.

          * multi_device: (boolean) Whether or not the block's rendering obtained via block_url has support
            for multiple devices.
            Returned only if "multi_device" is included in the "fields" parameter.

        * navigation: A dictionary that maps block IDs to a collection of navigation information about each block.
          Each block contains the following fields. Returned only if using the "navigation" endpoint.

          * descendants: (list) A list of IDs of the children of the block if the block's depth in the
            course hierarchy is less than the navigation_depth.  Otherwise, a list of IDs of the aggregate descendants
            of the block.

        * blocks+navigation: A dictionary that combines both the blocks and navigation data.
          Returned only if using the "blocks+navigation" endpoint.

    """
    class RequestInfo(object):
        """
        A class for encapsulating the request information, including what optional fields are requested.
        """
        DEFAULT_FIELDS = "children,graded,format,multi_device"

        def __init__(self, request, course):
            self.request = request
            self.course = course
            self.field_data_cache = None

            # check what fields are requested
            try:
                # fields
                self.fields = set(request.GET.get('fields', self.DEFAULT_FIELDS).split(","))

                # block_count
                self.block_count = request.GET.get('block_count', "")
                self.block_count = (
                    self.block_count.split(",") if self.block_count else []
                )

                # navigation_depth
                # See docstring for why we default to 3.
                self.navigation_depth = int(request.GET.get('navigation_depth', '3'))

                # block_json
                self.block_json = json.loads(request.GET.get('block_json', "{}"))
                if self.block_json and not isinstance(self.block_json, dict):
                    raise ParseError
            except:
                raise ParseError

    class ResultData(object):
        """
        A class for encapsulating the result information, specifically the blocks and navigation data.
        """
        def __init__(self, return_blocks, return_nav):
            self.blocks = {}
            self.navigation = {}
            if return_blocks and return_nav:
                self.navigation = self.blocks

        def update_response(self, response, return_blocks, return_nav):
            """
            Updates the response object with result information.
            """
            if return_blocks and return_nav:
                response["blocks+navigation"] = self.blocks
            elif return_blocks:
                response["blocks"] = self.blocks
            elif return_nav:
                response["navigation"] = self.navigation

    class BlockInfo(object):
        """
        A class for encapsulating a block's information as needed during traversal of a block hierarchy.
        """
        def __init__(self, block, request_info, parent_block_info=None):
            # the block for which the recursion is being computed
            self.block = block

            # the type of the block
            self.type = block.category

            # the block's depth in the block hierarchy
            self.depth = 0

            # the block's children
            self.children = []

            # descendants_of_parent: the list of descendants for this block's parent
            self.descendants_of_parent = []
            self.descendants_of_self = []

            # if a parent block was provided, update this block's data based on the parent's data
            if parent_block_info:
                # increment this block's depth value
                self.depth = parent_block_info.depth + 1

                # set this blocks' descendants_of_parent
                self.descendants_of_parent = parent_block_info.descendants_of_self

                # add ourselves to the parent's children, if requested.
                if 'children' in request_info.fields:
                    parent_block_info.value.setdefault("children", []).append(unicode(block.location))

            # the block's data to include in the response
            self.value = {
                "id": unicode(block.location),
                "type": self.type,
                "display_name": block.display_name,
                "web_url": reverse(
                    "jump_to",
                    kwargs={"course_id": unicode(request_info.course.id), "location": unicode(block.location)},
                    request=request_info.request,
                ),
                "block_url": reverse(
                    "courseware.views.render_xblock",
                    kwargs={"usage_key_string": unicode(block.location)},
                    request=request_info.request,
                ),
            }

    @view_course_access(depth=None)
    def list(self, request, course, return_blocks=True, return_nav=True, *args, **kwargs):
        """
        REST API endpoint for listing all the blocks and/or navigation information in the course,
        while regarding user access and roles.

        Arguments:
            request - Django request object
            course - course module object
            return_blocks - If true, returns the blocks information for the course.
            return_nav - If true, returns the navigation information for the course.
        """
        # set starting point
        start_block = course

        # initialize request and result objects
        request_info = self.RequestInfo(request, course)
        result_data = self.ResultData(return_blocks, return_nav)

        # create and populate a field data cache by pre-fetching for the course (with depth=None)
        request_info.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, request.user, course, depth=None,
        )

        # start the recursion with the start_block
        self.recurse_blocks_nav(request_info, result_data, self.BlockInfo(start_block, request_info))

        # return response
        response = {"root": unicode(start_block.location)}
        result_data.update_response(response, return_blocks, return_nav)
        return Response(response)

    def recurse_blocks_nav(self, request_info, result_data, block_info):
        """
        A depth-first recursive function that supports calculation of both the list of blocks in the course
        and the navigation information up to the requested navigation_depth of the course.

        Arguments:
            request_info - Object encapsulating the request information.
            result_data - Running result data that is updated during the recursion.
            block_info - Information about the current block in the recursion.
        """
        # bind user data to the block
        block_info.block = get_module_for_descriptor(
            request_info.request.user,
            request_info.request,
            block_info.block,
            request_info.field_data_cache,
            request_info.course.id,
            course=request_info.course
        )

        # verify the user has access to this block
        if (block_info.block is None or not has_access(
                request_info.request.user,
                'load',
                block_info.block,
                course_key=request_info.course.id
        )):
            return

        # add the block's value to the result
        result_data.blocks[unicode(block_info.block.location)] = block_info.value

        # descendants
        self.update_descendants(request_info, result_data, block_info)

        # children: recursively call the function for each of the children, while supporting dynamic children.
        if block_info.block.has_children:
            block_info.children = get_dynamic_descriptor_children(block_info.block, request_info.request.user.id)
            for child in block_info.children:
                self.recurse_blocks_nav(
                    request_info,
                    result_data,
                    self.BlockInfo(child, request_info, parent_block_info=block_info)
                )

        # block count
        self.update_block_count(request_info, result_data, block_info)

        # block JSON data
        self.add_block_json(request_info, block_info)

        # multi-device support
        if 'multi_device' in request_info.fields:
            block_info.value['multi_device'] = block_info.block.has_support(
                getattr(block_info.block, 'student_view', None),
                'multi_device'
            )

        # additional fields
        self.add_additional_fields(request_info, block_info)

    def update_descendants(self, request_info, result_data, block_info):
        """
        Updates the descendants data for the current block.

        The current block is added to its parent's descendants if it is visible in the navigation
        (i.e., the 'hide_from_toc' setting is False).

        Additionally, the block's depth is compared with the navigation_depth parameter to determine whether the
        descendants of the block should be added to its own descendants (if block.depth <= navigation_depth)
        or to the descendants of the block's parents (if block.depth > navigation_depth).

        block_info.descendants_of_self is the list of descendants that is passed to this block's children.
        It should be either:
            descendants_of_parent - if this block's depth is greater than the requested navigation_depth.
            a dangling [] - if this block's hide_from_toc is True.
            a referenced [] in navigation[block.location]["descendants"] - if this block's depth is within
               the requested navigation depth.
        """
        # Blocks with the 'hide_from_toc' setting are accessible, just not navigatable from the table-of-contents.
        # If the 'hide_from_toc' setting is set on the block, do not add this block to the parent's descendants
        # list and let the block's descendants add themselves to a dangling (unreferenced) descendants list.
        if not block_info.block.hide_from_toc:
            # add this block to the parent's descendants
            block_info.descendants_of_parent.append(unicode(block_info.block.location))

            # if this block's depth in the hierarchy is greater than the requested navigation depth,
            # have the block's descendants add themselves to the parent's descendants.
            if block_info.depth > request_info.navigation_depth:
                block_info.descendants_of_self = block_info.descendants_of_parent

            # otherwise, have the block's descendants add themselves to this block's descendants by
            # referencing/attaching descendants_of_self from this block's navigation value.
            else:
                result_data.navigation.setdefault(
                    unicode(block_info.block.location), {}
                )["descendants"] = block_info.descendants_of_self

    def update_block_count(self, request_info, result_data, block_info):
        """
        For all the block types that are requested to be counted, include the count of that block type as
        aggregated from the block's descendants.

        Arguments:
            request_info - Object encapsulating the request information.
            result_data - Running result data that is updated during the recursion.
            block_info - Information about the current block in the recursion.
        """
        for b_type in request_info.block_count:
            block_info.value.setdefault("block_count", {})[b_type] = (
                sum(
                    result_data.blocks.get(unicode(child.location), {}).get("block_count", {}).get(b_type, 0)
                    for child in block_info.children
                ) +
                (1 if b_type == block_info.type else 0)
            )

    def add_block_json(self, request_info, block_info):
        """
        If the JSON data for this block's type is requested, and the block supports the 'student_view_json'
        method, add the response from the 'student_view_json" method as the data for the block.
        """
        if block_info.type in request_info.block_json:
            if getattr(block_info.block, 'student_view_data', None):
                block_info.value["block_json"] = block_info.block.student_view_data(
                    context=request_info.block_json[block_info.type]
                )

    # A mapping of API-exposed field names to xBlock field names and API field defaults.
    BlockApiField = namedtuple('BlockApiField', 'block_field_name api_field_default')
    FIELD_MAP = {
        'graded': BlockApiField(block_field_name='graded', api_field_default=False),
        'format': BlockApiField(block_field_name='format', api_field_default=None),
    }

    def add_additional_fields(self, request_info, block_info):
        """
        Add additional field names and values of the block as requested in the request_info.
        """
        for field_name in request_info.fields:
            if field_name in self.FIELD_MAP:
                block_info.value[field_name] = getattr(
                    block_info.block,
                    self.FIELD_MAP[field_name].block_field_name,
                    self.FIELD_MAP[field_name].api_field_default,
                )

    def perform_authentication(self, request):
        """
        Ensures that the user is authenticated (e.g. not an AnonymousUser)
        """
        super(CourseBlocksAndNavigation, self).perform_authentication(request)
        if request.user.is_anonymous():
            raise AuthenticationFailed
