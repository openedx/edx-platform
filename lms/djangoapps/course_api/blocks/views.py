from django.core.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from lms.djangoapps.course_blocks.api import get_course_blocks, LMS_COURSE_TRANSFORMERS
from openedx.core.lib.api.view_utils import view_auth_classes, DeveloperErrorViewMixin

from transformers.blocks_api import BlocksAPITransformer
from transformers.block_counts import BlockCountsTransformer
from transformers.student_view import StudentViewTransformer
from .forms import BlockListGetForm
from .serializers import BlockSerializer


# TODO
# user not specified (-> staff)
# children field
# navigation to return descendants
# support hide_from_toc

@view_auth_classes()
class CourseBlocks(DeveloperErrorViewMixin, ListAPIView):
    """
    **Use Case**

        Returns the blocks of the course according to the requesting user's access level.

    **Example requests**:

        GET /api/courses/v1/blocks/<root_block_usage_id>/?depth=all
        GET /api/courses/v1/blocks/<usage_id>/?
            user=anjali,
            &fields=graded,format,multi_device,
            &block_counts=video,
            &student_view_data=video,
            &student_view_data.video=mobile_low

    **Parameters**:

        * student_view_data: (list) Indicates for which block types to return student_view_data.

          Example: student_view_data=video

        * block_counts: (list) Indicates for which block types to return the aggregate count of the blocks.

          Example: block_counts=video,problem

        * fields: (list) Indicates which additional fields to return for each block.
          Default is children,graded,format,student_view_multi_device

          Example: fields=graded,format,student_view_multi_device

        * depth (integer or all) Indicates how deep to traverse into the blocks hierarchy.
          A value of all means the entire hierarchy.
          Default is 0

          Example: depth=all

    **Response Values**

        The following fields are returned with a successful response.

        * root: The ID of the root node of the course blocks.

        * blocks: A dictionary that maps block usage IDs to a collection of information about each block.
          Each block contains the following fields.

          * id: (string) The usage ID of the block.

          * type: (string) The type of block. Possible values include course, chapter, sequential, vertical, html,
            problem, video, and discussion. The type can also be the name of a custom type of block used for the course.

          * display_name: (string) The display name of the block.

          * children: (list) If the block has child blocks, a list of IDs of the child blocks.
            Returned only if the "children" input parameter is True.

          * block_counts: (dict) For each block type specified in the block_counts parameter to the endpoint, the
            aggregate number of blocks of that type for this block and all of its descendants.
            Returned only if the "block_counts" input parameter contains this block's type.

          * graded (boolean) Whether or not the block or any of its descendants is graded.
            Returned only if "graded" is included in the "fields" parameter.

          * format: (string) The assignment type of the block.
            Possible values can be "Homework", "Lab", "Midterm Exam", and "Final Exam".
            Returned only if "format" is included in the "fields" parameter.

          * student_view_data: (dict) The JSON data for this block.
            Returned only if the "student_view_data" input parameter contains this block's type.

          * student_view_url: (string) The URL to retrieve the HTML rendering of this block's student view.
            The HTML could include CSS and Javascript code. This field can be used in combination with the
            student_view_multi_device field to decide whether to display this content to the user.

            This URL can be used as a fallback if the student_view_data for this block type is not supported by
            the client or the block.

          * student_view_multi_device: (boolean) Whether or not the block's rendering obtained via block_url has support
            for multiple devices.

            Returned only if "student_view_multi_device" is included in the "fields" parameter.

          * lms_web_url: (string) The URL to the navigational container of the xBlock on the web LMS.
            This URL can be used as a further fallback if the student_view_url and the student_view_data fields
            are not supported.

    """
    def list(self, request, usage_key_string):
        """
        REST API endpoint for listing all the blocks and/or navigation information in the course,
        while regarding user access and roles.

        Arguments:
            request - Django request object
            course - course module object
        """
        requested_params = request.GET.copy()
        requested_params.update({'usage_key': usage_key_string})
        params = BlockListGetForm(requested_params, initial={'request': request})
        if not params.is_valid():
            raise ValidationError(params.errors)

        blocks_api_transformer = BlocksAPITransformer(
            params.cleaned_data.get(BlockCountsTransformer.BLOCK_COUNTS, []),
            params.cleaned_data.get(StudentViewTransformer.STUDENT_VIEW_DATA, []),
        )
        blocks = get_course_blocks(
            params.cleaned_data['user'],
            params.cleaned_data['usage_key'],
            transformers=LMS_COURSE_TRANSFORMERS + [blocks_api_transformer],
        )

        return Response(
            BlockSerializer(
                blocks,
                context={
                    'request': request,
                    'block_structure': blocks,
                    'requested_fields': params.cleaned_data['requested_fields'],
                },
                many=True,
            ).data
        )
