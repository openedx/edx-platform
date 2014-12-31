"""
Implementation of the RESTful endpoints for the Course About API.

"""
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from course_about import api


class CourseAboutThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the Course About API."""
    # TODO Limit based on expected throughput  # pylint: disable=fixme
    rate = '50/second'


class CourseAboutView(APIView):
    """ RESTful Course About API view.

    Used to retrieve JSON serialized Course About information.

    """
    authentication_classes = []
    permission_classes = []
    throttle_classes = CourseAboutThrottle,

    def get(self, request, course_id=None):  # pylint: disable=unused-argument
        """Retrieve Course About information for the given course.

        HTTP Endpoint for retrieving Course About information.  Returns a JSON serialized representation of
        the metadata.

        """
        # TODO: Implement all request handling and error handling.
        return api.get_course_about_details(course_id)
