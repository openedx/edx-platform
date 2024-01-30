"""HomePageCoursesViewV2 APIView for getting content available to the logged in user."""
import edx_api_doc_tools as apidocs
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from openedx.core.lib.api.view_utils import view_auth_classes

from cms.djangoapps.contentstore.utils import get_course_context_v2
from cms.djangoapps.contentstore.rest_api.v2.serializers import CourseHomeTabSerializerV2


@view_auth_classes(is_authenticated=True)
class HomePageCoursesViewV2(APIView):
    """View for getting all courses available to the logged in user."""

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "org",
                apidocs.ParameterLocation.QUERY,
                description="Query param to filter by course org",
            ),
            apidocs.string_parameter(
                "search",
                apidocs.ParameterLocation.QUERY,
                description="Query param to filter by course name, org, or number",
            ),
            apidocs.string_parameter(
                "order",
                apidocs.ParameterLocation.QUERY,
                description="Query param to order by course name, org, or number",
            ),
            apidocs.string_parameter(
                "active_only",
                apidocs.ParameterLocation.QUERY,
                description="Query param to filter by active courses only",
            ),
            apidocs.string_parameter(
                "archived_only",
                apidocs.ParameterLocation.QUERY,
                description="Query param to filter by archived courses only",
            ),
        ],
        responses={
            200: CourseHomeTabSerializerV2,
            401: "The requester is not authenticated.",
        },
    )
    def get(self, request: Request):
        """
        Get an object containing all courses.

        **Example Request**

            GET /api/contentstore/v2/home/courses

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains keys that
        are the course's home.

        **Example Response**

        ```json
        {
            "courses": [
                 {
                    "course_key": "course-v1:edX+E2E-101+course",
                    "display_name": "E2E Test Course",
                    "lms_link": "//localhost:18000/courses/course-v1:edX+E2E-101+course",
                    "number": "E2E-101",
                    "org": "edX",
                    "rerun_link": "/course_rerun/course-v1:edX+E2E-101+course",
                    "run": "course",
                    "url": "/course/course-v1:edX+E2E-101+course"
                },
            ],
            "in_process_course_actions": [],
        }
        ```
        """

        courses, in_process_course_actions = get_course_context_v2(request)
        courses_context = {
            "courses": courses,
            "in_process_course_actions": in_process_course_actions,
        }
        serializer = CourseHomeTabSerializerV2(courses_context)
        return Response(serializer.data)
