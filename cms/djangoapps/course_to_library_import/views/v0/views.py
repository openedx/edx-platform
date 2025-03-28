"""
API v0 views.
"""
from lxml import etree

from django.shortcuts import get_object_or_404

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2

from rest_framework.permissions import IsAdminUser
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.course_to_library_import import api
from cms.djangoapps.course_to_library_import.constants import COURSE_TO_LIBRARY_IMPORT_PURPOSE
from cms.djangoapps.course_to_library_import.models import CourseToLibraryImport
from cms.djangoapps.course_to_library_import.views.v0.serializers import CourseToLibraryImportSerializer
from openedx.core.djangoapps.content_libraries.api import ContentLibrary
from openedx.core.djangoapps.content_staging import api as content_staging_api
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from .serializers import ImportBlocksSerializer


class ImportBlocksView(APIView):
    """
    Import blocks from a course to a library.
    """

    permission_classes = (IsAdminUser,)
    serializer_class = ImportBlocksSerializer

    def post(self, request, *args, **kwargs):
        """
        Import blocks from a course to a library.

        API endpoint: POST /api/course_to_library_import/v0/import_blocks/

        Request:
        {
            "library_key": "lib:org:code:run",
            "course_id": "course-v1:org+course+run",
            "usage_ids": ["block-v1:org+course+run+type@problem+block@12345"],
            "import_id": "78df3b2c-4e5a-4d6b-8c7e-1f2a3b4c5d6e",
            "composition_level": "xblock",
            "override": false
        }

        Response:
        {
            "status": "success"
        }
        """
        data = self.serializer_class(data=request.data)
        data.is_valid(raise_exception=True)

        api.import_library_from_staged_content(
            library_key=data.validated_data['library_key'],
            user_id=request.user.pk,
            usage_ids=data.validated_data['usage_ids'],
            course_id=data.validated_data['course_id'],
            import_id=data.validated_data['import_id'],
            composition_level=data.validated_data['composition_level'],
            override=data.validated_data['override'],
        )
        return Response({'status': 'success'})


class CreateCourseToLibraryImportView(CreateAPIView):
    """
    **Use Case**
        Allows to create course to library import.
    **Example Request**
        POST /api/course_to_library_import/v0/create_import/<content_library_id>/
        **POST Parameters**
            * course_ids (list) - A list of course IDs whose content will be saved
            in Staged Content for further import.
    **POST Response Values**
        If the request is successful, an HTTP 201 "Created" response
        is returned with the newly created CourseToLibraryImport details.
        The HTTP 201 response has the following values.
        {
          "course_ids": ["course-v1:edX+DemoX+Demo_Course", "course-v1:edX+DemoX+Demo_Course2"],
          "status": "pending",
          "library_key": "lib:edX:1",
          "uuid": "89b71d29-2135-4cf2-991d-e4e13b5a959a"
        }
    """

    serializer_class = CourseToLibraryImportSerializer

    permission_classes = (IsAdminUser,)
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    def get_serializer_context(self) -> dict:
        """
        Add library_id to the serializer context.
        """
        context = super().get_serializer_context()
        context['content_library_id'] = self.kwargs['content_library_id']
        return context

    def post(self, request, *args, **kwargs):
        """
        Create course to library import.
        """
        library_key = LibraryLocatorV2.from_string(self.kwargs['content_library_id'])
        try:
            ContentLibrary.objects.get_by_key(library_key)
        except ContentLibrary.DoesNotExist:
            return Response(status=404)
        else:
            return super().post(request, *args, **kwargs)


class GetCourseStructureToLibraryImportView(RetrieveAPIView):
    """
    **Use Case**
        Get the course structure saved when creating the import.
    **Example Request**
        GET /api/course_to_library_import/v0/get_import/{course-to-library-uuid}/
    **GET Response Values**
        The query returns a list of hierarchical structures of
        courses that are related to the import in the format:
          [
            course_id1: [
              {
                chapter_id1: chapter_display_name,
                children: [
                  {
                    sequential_id1: chapter_display_name
                    children: [...]
                  }
                ]
              },
              {
                chapter_id2: chapter_display_name,
                children: [
                  {
                    sequential_id2: chapter_display_name
                    children: [...]
                  }
                ]
              },
            ],
            ...
         ]
    **Example GET Response**
        {
          "course-v1:edX+DemoX+Demo_Course": [
            {
              "block-v1:edX+DemoX+Demo_Course+type@chapter+block@3f8c073c6bf74096b9a4033227de01d3": "Section 1",
              "children": [
                {
                  "block-v1:edX+DemoX+Demo_Course+type@sequential+block@194836ad915645d684828d4e48dbc09e": "Subsection",
                  "children": [
                    {
                      "block-v1:edX+DemoX+Demo_Course+type@vertical+block@07a5b2fb186f4a47ac2d1afe3ef91850": "Unit 1",
                      "children": [
                        {
                          "block-v1:edX+DemoX+Demo_Course+type@problem+block@a9c78c9ad3a148c2939091f5fbdd0eeb": "Block"
                        },
                        {
                          "block-v1:edX+DemoX+Demo_Course+type@video+block@195f37e99f1b4fedb607c621f239debb": "Video"
                        },
                        {
                          "block-v1:edX+DemoX+Demo_Course+type@lti+block@1700d68eae7d438aacf66fc8203efcda": "lti"
                        }
                      ]
                    },
                    {
                      "block-v1:edX+DemoX+Demo_Course+type@vertical+block@c6b19a1c7136483f9dd037a14641c289": "Unit 2",
                      "children": [
                        {
                          "block-v1:edX+DemoX+Demo_Course+type@html+block@330fcd9b9fa6476b8d39629dbc5cf20b": "HTML"
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
    """

    queryset = CourseToLibraryImport.objects.all()
    lookup_field = 'uuid'
    lookup_url_kwarg = 'course_to_lib_uuid'

    permission_classes = (IsAdminUser,)
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    def get(self, request, *args, **kwargs) -> Response:
        """
        Get the course structure saved when creating the import.
        """
        ctl = get_object_or_404(CourseToLibraryImport, uuid=self.kwargs['course_to_lib_uuid'])
        courses = {}
        for course_id in ctl.course_ids.split():
            courses[course_id] = self.get_structure_for_course_from_stage_content(course_id)

        return Response(courses)

    def get_structure_for_course_from_stage_content(self, course_id: str) -> list[dict]:
        """
        Build course structure of the course from staged content.

        This method retrieves the staged content for the given course ID and constructs
        a hierarchical structure representing the course's content. The structure is built
        by parsing the OLX  fragments and mapping them to their respective usage keys.
        """
        parser = etree.XMLParser(strip_cdata=False)
        staged_content = content_staging_api.get_ready_staged_content_by_user_and_purpose(
            self.request.user.pk, COURSE_TO_LIBRARY_IMPORT_PURPOSE.format(course_id=course_id)
        )

        courses_structure = []
        for staged_content_item in staged_content:
            staged_keys = [UsageKey.from_string(key) for key in staged_content_item.tags.keys()]
            block_id_usage_key_map = {key.block_id: key for key in staged_keys}
            olx_fragment = etree.fromstring(staged_content_item.olx, parser=parser)
            courses_structure.append(
                self.build_hierarchical_course_fragment_structure(olx_fragment, block_id_usage_key_map)
            )

        return courses_structure

    def build_hierarchical_course_fragment_structure(
        self,
        olx_fragment: 'etree._Element',
        block_id_usage_key_map: dict[str, UsageKey]
    ) -> dict[str, list[dict[str, dict[str, str]]]] | None:
        """
        Creates a hierarchical structure of course parts recursively.

        This method takes an OLX fragment and a mapping of block IDs to usage keys,
        and constructs a nested dictionary representing the hierarchical structure
        of the course. It processes each OLX element, mapping it to its usage key,
        and recursively processes its children if they exist.
        """
        usage_key = block_id_usage_key_map.get(olx_fragment.get('url_name'))
        if usage_key:
            node_dict = {
                str(usage_key): olx_fragment.get('display_name') or olx_fragment.tag,
            }

            children = olx_fragment.getchildren()
            if children and olx_fragment.tag in ('chapter', 'sequential', 'vertical'):
                node_dict.update({
                    'children': [
                        self.build_hierarchical_course_fragment_structure(child, block_id_usage_key_map)
                        for child in children
                    ]
                })

            return node_dict
