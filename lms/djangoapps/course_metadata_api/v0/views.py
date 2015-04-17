"""
The views.py module contains the RESTful interface for the Course Metadata API application
"""

import logging

from django.conf import settings

from rest_framework.generics import RetrieveAPIView, ListAPIView

from openedx.core.lib.api.serializers import PaginationSerializer

from course_metadata_api.v0 import serializers

class CourseList(ListAPIView):
    """
    **Use Case**

        Get a paginated list of courses in the edX Platform.

        The list can be filtered by course_id.

        Each page in the list can contain up to 10 courses.

    **Example Requests**

          GET /api/course_metadata/v0/courses/?org_id={org_id}

          GET /api/course_metadata/v0/courses/?org_id={org_id}&course_id={course_id1},{course_id2}

    **Response Values**

        * count: The number of courses in the edX platform.

        * next: The URI to the next page of courses.

        * previous: The URI to the previous page of courses.

        * num_pages: The number of pages listing courses.

        * results:  A list of courses returned. Each collection in the list
          contains these fields.

            * uri: (string), The fully-qualified address for the course

            * course_id: (string), The unique identifier for the course

            * org: (string), The organization offering the course

            * course: (string), The course number

            * run: (string), The run of the course

            * name: (string), The name of the course

            * start: (datetime), The start date of the course

            * end: (datetime), The end date of the course

            * short_description: (string), A brief description for the course

            * media: (dict), A collection of media metadata for the course (image, video, etc.)

            * staff: (array), A list of instructors and other staff for the course
    """
    paginate_by = 10
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = serializers.CourseSerializer

    def get_queryset(self):
        # Ensure org_id filter was provided (no unfiltered access)

        # Pass baton to api.py for processing

            # Filter down by course_id list, if provided

            # Query Elasticsearch instead of modulestore (via data.py)

            # Ensure only course descriptors are included in the matches

            # Ensure only courses flagged as 'viewable' are returned

            # Sort the results in a predictable manner.

        # Return response to caller


class CourseDetail(CourseViewMixin, RetrieveAPIView):
    """
    **Use Case**

        Get details for a specific course.

    **Example Request**:

        GET /api/course_metadata/v0/courses/{course_id}/

    **Response Values**

        * uri: (string), The fully-qualified address for the course

        * course_id: (string), The unique identifier for the course

        * org: (string), The organization offering the course

        * course: (string), The course number

        * run: (string), The run of the course

        * name: (string), The name of the course

        * start: (datetime), The start date of the course

        * end: (datetime), The end date of the course

        * short_description: (string), A brief description for the course

        * media: (dict), A collection of media metadata for the course (image, video, etc.)

        * staff: (array), A list of instructors and other staff for the course

    """

    serializer_class = serializers.CourseSerializer

    def get_object(self, queryset=None):
        # Pass baton to api.py for processing
        # Return response to caller
