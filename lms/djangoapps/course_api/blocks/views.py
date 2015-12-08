"""
CourseBlocks API views
"""
from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.lib.api.view_utils import view_auth_classes, DeveloperErrorViewMixin
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .api import get_blocks
from .forms import BlockListGetForm


@view_auth_classes()
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
            &requested_fields=graded,format,student_view_multi_device
            &block_counts=video
            &student_view_data=video

    **Parameters**:

        * username: (string) The name of the user on whose behalf we want to
          see the data.

          Example: username=anjali

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

    **Response Values**

        The following fields are returned with a successful response.

        * root: The ID of the root node of the course blocks.

        * blocks: A dictionary that maps block usage IDs to a collection of
          information about each block.  Each block contains the following
          fields.

          * id: (string) The usage ID of the block.

          * type: (string) The type of block. Possible values include course,
            chapter, sequential, vertical, html, problem, video, and
            discussion. The type can also be the name of a custom type of block
            used for the course.

          * display_name: (string) The display name of the block.

          * children: (list) If the block has child blocks, a list of IDs of
            the child blocks.  Returned only if "children" is included in the
            "requested_fields" parameter.

          * block_counts: (dict) For each block type specified in the
            block_counts parameter to the endpoint, the aggregate number of
            blocks of that type for this block and all of its descendants.
            Returned only if the "block_counts" input parameter contains this
            block's type.

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

          * student_view_multi_device: (boolean) Whether or not the block's
            rendering obtained via block_url has support for multiple devices.
            Returned only if "student_view_multi_device" is included in the
            "requested_fields" parameter.

          * lms_web_url: (string) The URL to the navigational container of the
            xBlock on the web LMS.  This URL can be used as a further fallback
            if the student_view_url and the student_view_data fields are not
            supported.

    """

    def list(self, request, usage_key_string):  # pylint: disable=arguments-differ
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
            return Response(
                get_blocks(
                    request,
                    params.cleaned_data['usage_key'],
                    params.cleaned_data['user'],
                    params.cleaned_data['depth'],
                    params.cleaned_data.get('nav_depth'),
                    params.cleaned_data['requested_fields'],
                    params.cleaned_data.get('block_counts', []),
                    params.cleaned_data.get('student_view_data', []),
                    params.cleaned_data['return_type']
                )
            )
        except ItemNotFoundError as exception:
            raise Http404("Block not found: {}".format(exception.message))


@view_auth_classes()
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
            &requested_fields=graded,format,student_view_multi_device
            &block_counts=video
            &student_view_data=video

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

    def list(self, request):  # pylint: disable=arguments-differ
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
            raise ValidationError("'{}' is not a valid course key.".format(unicode(course_key_string)))
        return super(BlocksInCourseView, self).list(request, course_usage_key)
