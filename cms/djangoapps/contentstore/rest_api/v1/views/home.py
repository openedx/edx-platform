""" API Views for course home """

import edx_api_doc_tools as apidocs
from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from openedx.core.lib.api.view_utils import view_auth_classes

from ....utils import get_home_context, get_course_context, get_library_context
from ..serializers import CourseHomeSerializer, CourseHomeTabSerializer, LibraryTabSerializer


@view_auth_classes(is_authenticated=True)
class HomePageView(APIView):
    """
    View for getting all courses and libraries available to the logged in user.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "org",
                apidocs.ParameterLocation.QUERY,
                description="Query param to filter by course org",
            )],
        responses={
            200: CourseHomeSerializer,
            401: "The requester is not authenticated.",
        },
    )
    def get(self, request: Request):
        """
        Get an object containing all courses and libraries on home page.

        **Example Request**

            GET /api/contentstore/v1/home

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains keys that
        are the course's home.

        **Example Response**

        ```json
        {
            "allow_course_reruns": true,
            "allow_to_create_new_org": true,
            "allow_unicode_course_id": false,
            "allowed_organizations": [],
            "archived_courses": [],
            "can_access_advanced_settings": true,
            "can_create_organizations": true,
            "course_creator_status": "granted",
            "courses": [],
            "in_process_course_actions": [],
            "libraries": [],
            "libraries_enabled": true,
            "optimization_enabled": true,
            "request_course_creator_url": "/request_course_creator",
            "rerun_creator_status": true,
            "show_new_library_button": true,
            "split_studio_home": false,
            "studio_name": "Studio",
            "studio_short_name": "Studio",
            "studio_request_email": "",
            "tech_support_email": "technical@example.com",
            "platform_name": "Your Platform Name Here"
            "user_is_active": true,
        }
        ```
        """

        home_context = get_home_context(request, True)
        home_context.update({
            'allow_to_create_new_org': settings.FEATURES.get('ENABLE_CREATOR_GROUP', True) and request.user.is_staff,
            'studio_name': settings.STUDIO_NAME,
            'studio_short_name': settings.STUDIO_SHORT_NAME,
            'studio_request_email': settings.FEATURES.get('STUDIO_REQUEST_EMAIL', ''),
            'tech_support_email': settings.TECH_SUPPORT_EMAIL,
            'platform_name': settings.PLATFORM_NAME,
            'user_is_active': request.user.is_active,
        })
        serializer = CourseHomeSerializer(home_context)
        return Response(serializer.data)


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

        active_courses, archived_courses, in_process_course_actions = get_course_context(request)
        courses_context = {
            "courses": active_courses,
            "archived_courses": archived_courses,
            "in_process_course_actions": in_process_course_actions,
        }
        serializer = CourseHomeTabSerializer(courses_context)
        return Response(serializer.data)


@view_auth_classes(is_authenticated=True)
class HomePageLibrariesView(APIView):
    """
    View for getting all courses and libraries available to the logged in user.
    """
    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "org",
                apidocs.ParameterLocation.QUERY,
                description="Query param to filter by course org",
            )],
        responses={
            200: LibraryTabSerializer,
            401: "The requester is not authenticated.",
        },
    )
    def get(self, request: Request):
        """
        Get an object containing all libraries on home page.

        **Example Request**

            GET /api/contentstore/v1/home/libraries

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains keys that
        are the course's home.

        **Example Response**

        ```json
        {
            "libraries": [
                {
                "display_name": "My First Library",
                "library_key": "library-v1:new+CPSPR",
                "url": "/library/library-v1:new+CPSPR",
                "org": "new",
                "number": "CPSPR",
                "can_edit": true
                }
            ],        }
        ```
        """

        library_context = get_library_context(request)
        serializer = LibraryTabSerializer(library_context)

        return Response(serializer.data)
