"""
Views for course info API
"""

import logging

from django.contrib.auth import get_user_model
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.static_replace import make_static_urls_absolute
from lms.djangoapps.courseware.courses import get_course_info_section_block
from lms.djangoapps.course_goals.models import UserActivity
from lms.djangoapps.course_api.views import CourseDetailView
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.lib.xblock_utils import get_course_update_items
from openedx.features.course_experience import ENABLE_COURSE_GOALS
from .serializers import CourseInfoDetailSerializer
from ..decorators import mobile_course_access, mobile_view

User = get_user_model()
log = logging.getLogger(__name__)


@mobile_view()
class CourseUpdatesList(generics.ListAPIView):
    """
    **Use Case**

        Get the content for course updates.

    **Example Request**

        GET /api/mobile/v0.5/course_info/{course_id}/updates

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK"
        response along with an array of course updates. Each course update
        contains the following values.

            * content: The content, as an HTML string, of the course update.
            * date: The date of the course update.
            * id: The unique identifier of the update.
            * status: Whether the update is visible or not.
    """

    @mobile_course_access()
    def list(self, request, course, *args, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        course_updates_block = get_course_info_section_block(request, request.user, course, 'updates')
        update_items = get_course_update_items(course_updates_block)

        updates_to_show = [
            update for update in update_items
            if update.get("status") != "deleted"
        ]

        for item in updates_to_show:
            item['content'] = apply_wrappers_to_content(item['content'], course_updates_block, request)

        return Response(updates_to_show)


@mobile_view()
class CourseHandoutsList(generics.ListAPIView):
    """
    **Use Case**

        Get the HTML for course handouts.

    **Example Request**

        GET /api/mobile/v0.5/course_info/{course_id}/handouts

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK"
        response along with the following value.

        * handouts_html: The HTML for course handouts.
    """

    @mobile_course_access()
    def list(self, request, course, *args, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        course_handouts_block = get_course_info_section_block(request, request.user, course, 'handouts')
        if course_handouts_block:
            if course_handouts_block.data == "<ol></ol>":
                handouts_html = None
            else:
                handouts_html = apply_wrappers_to_content(course_handouts_block.data, course_handouts_block, request)
            return Response({'handouts_html': handouts_html})
        else:
            # course_handouts_block could be None if there are no handouts
            return Response({'handouts_html': None})


def apply_wrappers_to_content(content, block, request):
    """
    Updates a piece of html content with the filter functions stored in its module system, then replaces any
    static urls with absolute urls.

    Args:
        content: The html content to which to apply the content wrappers generated for this module system.
        block: The block containing a reference to the module system which contains functions to apply to the
        content. These functions include:
            * Replacing static url's
            * Replacing course url's
            * Replacing jump to id url's
        request: The request, used to replace static URLs with absolute URLs.

    Returns: A piece of html content containing the original content updated by each wrapper.

    """
    content = block.runtime.service(block, "replace_urls").replace_urls(content)

    return make_static_urls_absolute(request, content)


@mobile_view()
class CourseGoalsRecordUserActivity(APIView):
    """
    API that allows the mobile_apps to record activity for course goals to the user activity table
    """

    def post(self, request, *args, **kwargs):
        """
        Handle the POST request

        Populate the user activity table.
        """
        user_id = request.data.get('user_id')
        course_key = request.data.get('course_key')

        if not user_id or not course_key:
            log.error('User id and course key are required. %s %s', user_id, course_key)
            return Response(
                'User id and course key are required',
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = int(user_id)
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            log.error('Provided user id does not correspond to an existing user %s', user_id)
            return Response(
                'Provided user id does not correspond to an existing user',
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            course_key = CourseKey.from_string(course_key)
        except InvalidKeyError:
            log.error('Provided course key is not valid %s', course_key)
            return Response(
                'Provided course key is not valid',
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not ENABLE_COURSE_GOALS.is_enabled(course_key):
            log.warning('For this mobile request, user activity is not enabled for this user {} and course {}'.format(
                str(user_id), str(course_key))
            )
            return Response(status=(200))

        # Populate user activity for tracking progress towards a user's course goals
        UserActivity.record_user_activity(user, course_key)
        return Response(status=(200))


@view_auth_classes(is_authenticated=False)
class CourseInfoDetailView(CourseDetailView):
    """
        **Use Cases**

            Request details for a course

        **Example Requests**

            GET /api/mobile/v3/course_info/{course_key}/info

        **Response Values**

            Body consists of the following fields:

            * effort: A textual description of the weekly hours of effort expected
                in the course.
            * end: Date the course ends, in ISO 8601 notation
            * enrollment_end: Date enrollment ends, in ISO 8601 notation
            * enrollment_start: Date enrollment begins, in ISO 8601 notation
            * id: A unique identifier of the course; a serialized representation
                of the opaque key identifying the course.
            * media: An object that contains named media items.  Included here:
                * course_image: An image to show for the course.  Represented
                  as an object with the following fields:
                    * uri: The location of the image
            * name: Name of the course
            * number: Catalog number of the course
            * org: Name of the organization that owns the course
            * overview: A possibly verbose HTML textual description of the course.
                Note: this field is only included in the Course Detail view, not
                the Course List view.
            * short_description: A textual description of the course
            * start: Date the course begins, in ISO 8601 notation
            * start_display: Readably formatted start of the course
            * start_type: Hint describing how `start_display` is set. One of:
                * `"string"`: manually set by the course author
                * `"timestamp"`: generated from the `start` timestamp
                * `"empty"`: no start date is specified
            * pacing: Course pacing. Possible values: instructor, self
            * certificate_available_date (optional): Date the certificate will be available,
                in ISO 8601 notation if the `certificates.auto_certificate_generation`
                waffle switch is enabled
            * is_enrolled: (bool) Optional field. This field is not available for an anonymous user.
                Indicates if the user is enrolled in the course

            Deprecated fields:

            * blocks_url: Used to fetch the course blocks
            * course_id: Course key (use 'id' instead)

        **Parameters:**

            username (optional):
                The username of the specified user for whom the course data
                is being accessed. The username is not only required if the API is
                requested by an Anonymous user.

        **Returns**

            * 200 on success with above fields.
            * 400 if an invalid parameter was sent or the username was not provided
              for an authenticated request.
            * 401 unauthorized
            * 403 if a user who does not have permission to masquerade as
              another user specifies a username other than their own.
            * 404 if the course is not available or cannot be seen.

            Example response:

                {
                    "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                    "media": {
                        "course_image": {
                            "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                            "name": "Course Image"
                        }
                    },
                    "description": "An example course.",
                    "end": "2015-09-19T18:00:00Z",
                    "enrollment_end": "2015-07-15T00:00:00Z",
                    "enrollment_start": "2015-06-15T00:00:00Z",
                    "course_id": "edX/example/2012_Fall",
                    "name": "Example Course",
                    "number": "example",
                    "org": "edX",
                    "overview: "<p>A verbose description of the course.</p>"
                    "start": "2015-07-17T12:00:00Z",
                    "start_display": "July 17, 2015",
                    "start_type": "timestamp",
                    "pacing": "instructor",
                    "certificate_available_date": "2015-08-14T00:00:00Z",
                    "is_enrolled": true
                }
        """

    serializer_class = CourseInfoDetailSerializer
