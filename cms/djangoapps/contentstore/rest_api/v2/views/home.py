import edx_api_doc_tools as apidocs
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from openedx.core.lib.api.view_utils import view_auth_classes

from ....utils import get_course_context_v2
from ..serializers import CourseHomeTabSerializer


@view_auth_classes(is_authenticated=True)
class HomePageCoursesView(APIView):
    """
    View for getting all courses and libraries available to the logged in user.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "org",
                apidocs.ParameterLocation.QUERY,
                description="Query param to filter by course org",
            ),
            apidocs.string_parameter(
                "query",
                apidocs.ParameterLocation.QUERY,
                description="Query param to filter by course name, org, or number",
    )],
        responses={
            200: CourseHomeTabSerializer,
            401: "The requester is not authenticated.",
        },
    )
    def get(self, request: Request):
        """
        Get an object containing all courses.

        **Example Request**

            GET /api/contentstore/v1/home/courses

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains keys that
        are the course's home.

        **Example Response**

        ```json
        {
            "archived_courses": [
                {
                    "course_key": "course-v1:edX+P315+2T2023",
                    "display_name": "Quantum Entanglement",
                    "lms_link": "//localhost:18000/courses/course-v1:edX+P315+2T2023",
                    "number": "P315",
                    "org": "edX",
                    "rerun_link": "/course_rerun/course-v1:edX+P315+2T2023",
                    "run": "2T2023"
                    "url": "/course/course-v1:edX+P315+2T2023"
                },
            ],
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

        active_courses, archived_courses, in_process_course_actions = get_course_context_v2(request)
        courses_context = {
            "courses": active_courses,
            "archived_courses": archived_courses,
            "in_process_course_actions": in_process_course_actions,
        }
        serializer = CourseHomeTabSerializer(courses_context)
        return Response(serializer.data)
