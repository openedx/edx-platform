"""
Course API Views
"""

from django.http import Http404
from rest_framework.generics import ListAPIView, RetrieveAPIView

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.lib.api.paginators import NamespacedPageNumberPagination

from .api import course_detail, list_courses
from .serializers import CourseSerializer


class CourseDetailView(RetrieveAPIView):
    """
    **Use Cases**

        Request information on a course

    **Example Requests**

        GET /api/courses/v1/courses/{course_key}/

    **Response Values**

        Body consists of the following fields:

        * blocks_url: used to fetch the course blocks
        * media: An object that contains named media items.  Included here:
            * course_image: An image to show for the course.  Represented
              as an object with the following fields:
                * uri: The location of the image
                * name:
                * description:
                * type:
        * end: Date the course ends
        * enrollment_end: Date enrollment ends
        * enrollment_start: Date enrollment begins
        * course_id: Course key
        * name: Name of the course
        * number: Catalog number of the course
        * org: Name of the organization that owns the course
        * description: A textual description of the course
        * start: Date the course begins
        * start_display: Readably formatted start of the course
        * start_type: Hint describing how `start_display` is set. One of:
            * `"string"`: manually set
            * `"timestamp"`: generated form `start` timestamp
            * `"empty"`: the start date should not be shown

    **Parameters:**

        username (optional):
            The username of the specified user whose visible courses we
            want to see.  Defaults to the current user.

    **Returns**

        * 200 on success with above fields.
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
                "id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp"
            }
    """

    serializer_class = CourseSerializer
    lookup_url_kwarg = 'course_key_string'

    def get_object(self):
        """
        Return the requested course object, if the user has appropriate
        permissions.
        """

        username = self.request.query_params.get('username', self.request.user.username)
        course_key_string = self.kwargs[self.lookup_url_kwarg]
        try:
            course_key = CourseKey.from_string(course_key_string)
        except InvalidKeyError:
            raise Http404()

        return course_detail(self.request, username, course_key)


class CourseListView(ListAPIView):
    """
    **Use Cases**

        Request information on all courses visible to the specified user.

    **Example Requests**

        GET /api/courses/v1/courses/

    **Response Values**

        Body comprises a list of objects as returned by `CourseDetailView`.

    **Parameters**

        username (optional):
            The username of the specified user whose visible courses we
            want to see.  Defaults to the current user.

    **Returns**

        * 200 on success, with a list of course discovery objects as returned
          by `CourseDetailView`.
        * 403 if a user who does not have permission to masquerade as
          another user specifies a username other than their own.
        * 404 if the specified user does not exist, or the requesting user does
          not have permission to view their courses.

        Example response:

            [
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
                "id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp"
              }
            ]
    """

    pagination_class = NamespacedPageNumberPagination
    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        Return a list of courses visible to the user.
        """
        username = self.request.query_params.get('username', self.request.user.username)
        return list_courses(self.request, username)
