"""
CourseBlocks API views
"""


import six
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.cache import patch_response_headers
from django.utils.decorators import method_decorator
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from six import text_type

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .api import get_blocks
from .forms import BlockListGetForm


@method_decorator(transaction.non_atomic_requests, name='dispatch')
@view_auth_classes(is_authenticated=False)
class BlocksView(DeveloperErrorViewMixin, ListAPIView):
    """
    **Use Case**

        Returns the blocks within the requested block tree according to the
        requesting user's access level.

    **Example requests**:

        GET /api/courses/v1/blocks/<root_block_usage_id>/?depth=all
        GET /api/courses/v1/blocks/<usage_id>/?
            username=anjali
            &depth=all
            &requested_fields=graded,format,student_view_multi_device,lti_url,due
            &block_counts=video
            &student_view_data=video
            &block_types_filter=problem,html

    **Parameters**:

        * all_blocks: (boolean) Provide a value of "true" to return all
          blocks. Returns all blocks only if the requesting user has course
          staff permissions. Blocks that are visible only to specific learners
          (for example, based on group membership or randomized content) are
          all included. If all_blocks is not specified, you must specify the
          username for the user whose course blocks are requested.

        * username: (string) Required, unless ``all_blocks`` is specified.
          Specify the username for the user whose course blocks are requested.
          A blank/empty username can be used to request the blocks accessible
          to anonymous users (for public courses). Only users with course staff
          permissions can specify other users' usernames. If a username is
          specified, results include blocks that are visible to that user,
          including those based on group or cohort membership or randomized
          content assigned to that user.

          Example: username=anjali
                   username=''
                   username

        * student_view_data: (list) Indicates for which block types to return
          student_view_data.

          Example: student_view_data=video

        * block_counts: (list) Indicates for which block types to return the
          aggregate count of the blocks.

          Example: block_counts=video,problem

        * requested_fields: (list) Indicates which additional fields to return
          for each block.  For a list of available fields see under `Response
          Values -> blocks`, below.

          The following fields are always returned: id, type, display_name

          Example: requested_fields=graded,format,student_view_multi_device

        * depth: (integer or all) Indicates how deep to traverse into the blocks
          hierarchy.  A value of all means the entire hierarchy.

          Default is 0

          Example: depth=all

        * nav_depth: (integer)

          WARNING: nav_depth is not supported, and may be removed at any time.

          Indicates how far deep to traverse into the
          course hierarchy before bundling all the descendants.

          Default is 3 since typical navigational views of the course show a
          maximum of chapter->sequential->vertical.

          Example: nav_depth=3

        * return_type (string) Indicates in what data type to return the
          blocks.

          Default is dict. Supported values are: dict, list

          Example: return_type=dict

        * block_types_filter: (list) Requested types of blocks used to filter the final result
          of returned blocks. Possible values include sequential, vertical, html, problem,
          video, and discussion.

          Example: block_types_filter=vertical,html

    **Response Values**

        The following fields are returned with a successful response.

        * root: The ID of the root node of the requested course block
          structure.

        * blocks: A dictionary or list, based on the value of the
          "return_type" parameter. Maps block usage IDs to a collection of
          information about each block. Each block contains the following
          fields.

          * id: (string) The usage ID of the block.

          * type: (string) The type of block. Possible values the names of any
            XBlock type in the system, including custom blocks. Examples are
            course, chapter, sequential, vertical, html, problem, video, and
            discussion.

          * display_name: (string) The display name of the block.

          * children: (list) If the block has child blocks, a list of IDs of
            the child blocks.  Returned only if "children" is included in the
            "requested_fields" parameter.

          * completion: (float or None) The level of completion of the block.
            Its value can vary between 0.0 and 1.0 or be equal to None
            if block is not completable. Returned only if "completion"
            is included in the "requested_fields" parameter.

          * block_counts: (dict) For each block type specified in the
            block_counts parameter to the endpoint, the aggregate number of
            blocks of that type for this block and all of its descendants.

          * graded (boolean) Whether or not the block or any of its descendants
            is graded.  Returned only if "graded" is included in the
            "requested_fields" parameter.

          * format: (string) The assignment type of the block.  Possible values
            can be "Homework", "Lab", "Midterm Exam", and "Final Exam".
            Returned only if "format" is included in the "requested_fields"
            parameter.

          * student_view_data: (dict) The JSON data for this block.
            Returned only if the "student_view_data" input parameter contains
            this block's type.

          * student_view_url: (string) The URL to retrieve the HTML rendering
            of this block's student view.  The HTML could include CSS and
            Javascript code. This field can be used in combination with the
            student_view_multi_device field to decide whether to display this
            content to the user.

            This URL can be used as a fallback if the student_view_data for
            this block type is not supported by the client or the block.

          * student_view_multi_device: (boolean) Whether or not the HTML of
            the student view that is rendered at "student_view_url" supports
            responsive web layouts, touch-based inputs, and interactive state
            management for a variety of device sizes and types, including
            mobile and touch devices. Returned only if
            "student_view_multi_device" is included in the "requested_fields"
            parameter.

          * lms_web_url: (string) The URL to the navigational container of the
            xBlock on the web LMS.  This URL can be used as a further fallback
            if the student_view_url and the student_view_data fields are not
            supported.

          * lti_url: The block URL for an LTI consumer. Returned only if the
            "ENABLE_LTI_PROVIDER" Django settign is set to "True".

          * due: The due date of the block. Returned only if "due" is included
            in the "requested_fields" parameter.

          * show_correctness: Whether to show scores/correctness to learners for the current sequence or problem.
            Returned only if "show_correctness" is included in the "requested_fields" parameter.

          * Additional XBlock fields can be included in the response if they are
            configured via the COURSE_BLOCKS_API_EXTRA_FIELDS Django setting and
            requested via the "requested_fields" parameter.
    """

    def list(self, request, usage_key_string, hide_access_denials=False):  # pylint: disable=arguments-differ
        """
        REST API endpoint for listing all the blocks information in the course,
        while regarding user access and roles.

        Arguments:
            request - Django request object
            usage_key_string - The usage key for a block.
        """

        # validate request parameters
        requested_params = request.query_params.copy()
        requested_params.update({'usage_key': usage_key_string})
        params = BlockListGetForm(requested_params, initial={'requesting_user': request.user})
        if not params.is_valid():
            raise ValidationError(params.errors)

        try:
            response = Response(
                get_blocks(
                    request,
                    params.cleaned_data['usage_key'],
                    params.cleaned_data['user'],
                    params.cleaned_data['depth'],
                    params.cleaned_data.get('nav_depth'),
                    params.cleaned_data['requested_fields'],
                    params.cleaned_data.get('block_counts', []),
                    params.cleaned_data.get('student_view_data', []),
                    params.cleaned_data['return_type'],
                    params.cleaned_data.get('block_types_filter', None),
                    hide_access_denials=hide_access_denials,
                )
            )
            # If the username is an empty string, and not None, then we are requesting
            # data about the anonymous view of a course, which can be cached. In this
            # case we add the usual caching headers to the response.
            if params.cleaned_data.get('username', None) == '':
                patch_response_headers(response)
            return response
        except ItemNotFoundError as exception:
            raise Http404(u"Block not found: {}".format(text_type(exception)))


@view_auth_classes(is_authenticated=False)
class BlocksInCourseView(BlocksView):
    """
    **Use Case**

        Returns the blocks in the course according to the requesting user's
        access level.

    **Example requests**:

        GET /api/courses/v1/blocks/?course_id=<course_id>
        GET /api/courses/v1/blocks/?course_id=<course_id>
            &username=anjali
            &depth=all
            &requested_fields=graded,format,student_view_multi_device,lti_url
            &block_counts=video
            &student_view_data=video
            &block_types_filter=problem,html

    **Parameters**:

        This view redirects to /api/courses/v1/blocks/<root_usage_key>/ for the
        root usage key of the course specified by course_id.  The view accepts
        all parameters accepted by :class:`BlocksView`, plus the following
        required parameter

        * course_id: (string, required) The ID of the course whose block data
          we want to return

    **Response Values**

        Responses are identical to those returned by :class:`BlocksView` when
        passed the root_usage_key of the requested course.

        If the course_id is not supplied, a 400: Bad Request is returned, with
        a message indicating that course_id is required.

        If an invalid course_id is supplied, a 400: Bad Request is returned,
        with a message indicating that the course_id is not valid.
    """

    def list(self, request, hide_access_denials=False):  # pylint: disable=arguments-differ
        """
        Retrieves the usage_key for the requested course, and then returns the
        same information that would be returned by BlocksView.list, called with
        that usage key

        Arguments:
            request - Django request object
        """

        # convert the requested course_key to the course's root block's usage_key
        course_key_string = request.query_params.get('course_id', None)
        if not course_key_string:
            raise ValidationError('course_id is required.')

        try:
            course_key = CourseKey.from_string(course_key_string)
            course_usage_key = modulestore().make_course_usage_key(course_key)
        except InvalidKeyError:
            raise ValidationError(u"'{}' is not a valid course key.".format(six.text_type(course_key_string)))
        return super(BlocksInCourseView, self).list(request, course_usage_key, hide_access_denials=hide_access_denials)
