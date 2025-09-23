""" API Views for course home """

import edx_api_doc_tools as apidocs
from django.conf import settings
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from organizations import api as org_api
from openedx.core.lib.api.view_utils import view_auth_classes

from ....utils import get_home_context, get_library_context
from ..serializers import StudioHomeSerializer, LibraryTabSerializer


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
            200: StudioHomeSerializer,
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
            "allowed_organizations_for_libraries": [],
            "archived_courses": [],
            "can_access_advanced_settings": true,
            "can_create_organizations": true,
            "course_creator_status": "granted",
            "courses": [],
            "in_process_course_actions": [],
            "libraries": [],
            "libraries_enabled": true,
            "libraries_v1_enabled": true,
            "libraries_v2_enabled": true,
            "library_authoring_mfe_url": "//localhost:3001/course/course-v1:edX+P315+2T2023",
            "request_course_creator_url": "/request_course_creator",
            "rerun_creator_status": true,
            "show_new_library_button": true,
            "show_new_library_v2_button": true,
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
            # 'allow_to_create_new_org' is actually about auto-creating organizations
            # (e.g. when creating a course or library), so we add an additional test.
            'allow_to_create_new_org': (
                home_context['can_create_organizations'] and
                org_api.is_autocreate_enabled()
            ),
            'studio_name': settings.STUDIO_NAME,
            'studio_short_name': settings.STUDIO_SHORT_NAME,
            'studio_request_email': settings.FEATURES.get('STUDIO_REQUEST_EMAIL', ''),
            'tech_support_email': settings.TECH_SUPPORT_EMAIL,
            'platform_name': settings.PLATFORM_NAME,
            'user_is_active': request.user.is_active,
        })
        serializer = StudioHomeSerializer(home_context)
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
