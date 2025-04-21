"""
API v0 views.
"""
from lxml import etree

from django.shortcuts import get_object_or_404

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2
from rest_framework import status

from rest_framework.permissions import IsAdminUser
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.import_from_modulestore import api
from cms.djangoapps.import_from_modulestore.models import Import
from cms.djangoapps.import_from_modulestore.permissions import IsImportAuthor
from cms.djangoapps.import_from_modulestore.views.v0.serializers import ImportBlocksSerializer, ImportSerializer
from openedx.core.djangoapps.content_libraries.api import ContentLibrary
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser


class ImportBlocksView(APIView):
    """
    Import blocks from a course to a library.

    **Example Request**
        POST /api/import_from_modulestore/v0/import_blocks/

    **Example request data**
        ```
        {
            "usage_ids": ["block-v1:org+course+run+type@problem+block@12345"],
            "target_library": "lib:org:test",
            "import_uuid": "78df3b2c-4e5a-4d6b-8c7e-1f2a3b4c5d6e",
            "composition_level": "xblock",
            "override": false
        }
        ```

    **POST Parameters**
        - usage_ids (list): A list of usage IDs of the blocks to be imported.
        - target_library (str): The library to which the blocks will be imported.
        - import_uuid (str): The UUID of the import task.
        - composition_level (str): The composition level of the blocks to be imported.
        - override (bool): Whether to override existing blocks in the library.

    **Responses**
        - 200: Import blocks from a course to a library task successfully started.
        - 400: Invalid request data.
        - 401: Unauthorized.
        - 403: Forbidden, request user is not the author of the received import.
        - 404: Import not found.

    **Example Response**:
        ```
        {
            "status": "success"
        }
        ```
    """

    serializer_class = ImportBlocksSerializer

    permission_classes = (IsImportAuthor,)
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    def post(self, request, *args, **kwargs):
        """
        Import blocks from a course to a library.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        library_key = LibraryLocatorV2.from_string(serializer.validated_data['target_library'])
        try:
            content_library = ContentLibrary.objects.get_by_key(library_key)
        except ContentLibrary.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        api.import_course_staged_content_to_library(
            usage_ids=serializer.validated_data['usage_ids'],
            import_uuid=serializer.validated_data['import_uuid'],
            target_learning_package_id=content_library.learning_package_id,
            user_id=request.user.pk,
            composition_level=serializer.validated_data['composition_level'],
            override=serializer.validated_data['override'],
        )
        return Response({'status': 'success'})


class CreateCourseToLibraryImportView(CreateAPIView):
    """
    Create course to library import.

    **Example Request**
        POST /api/import_from_modulestore/v0/create_import/

    **Example request data**
        ```
        {
            "course_ids": ["course-v1:edX+DemoX+Demo_Course", "course-v1:edX+M12+2025"],
        }
        ```

    **POST Parameters**
        - course_ids (list): A list of course IDs for which imports will be created
            and content will be saved to the Staged Content.

    **Responses**
        - 200: Imports created successfully and saving content to Staged Content started.
        - 400: Invalid request data.
        - 401: Unauthorized.
        - 403: Forbidden.
        - 404: ContentLibrary not found.

    **Example Response**:
        ```
        [
            {
              "course_id": "course-v1:edX+DemoX+Demo_Course",
              "status": "staging",
              "uuid": "89b71d29-2135-4cf2-991d-e4e13b5a959a"
            },
            {
              "course_id": "course-v1:edX+M12+2025",
              "status": "not_started",
              "uuid": "0782921a-4b56-4972-aa3a-edd1c99de85f"
            },
        ]
        ```
    """

    serializer_class = ImportSerializer

    permission_classes = (IsAdminUser,)
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    def post(self, request, *args, **kwargs):
        """
        Create course to library import.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = (
            api.create_import(course_id, request.user.pk)
            for course_id in serializer.validated_data['course_ids']
        )

        serializer = self.get_serializer(result, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GetCourseStructureToLibraryImportView(RetrieveAPIView):
    """
    Get the course structure saved when creating the import.

    **Example Request**
        GET /api/import_from_modulestore/v0/get_import/{import_uuid}/

    **Responses**
        - 200: Course structure retrieved successfully.
        - 400: Invalid request data.
        - 401: Unauthorized.
        - 403: Forbidden.
        - 404: Import not found.

    **GET Response Values**
        The query returns a list of hierarchical structures of
        courses that are related to the import in the format:
          [
            {
              chapter_id1: chapter_display_name,
              children: [
                {
                  sequential_id1: chapter_display_name
                  children: [...]
                }
                ...
              ]
            },
            {
              chapter_id2: chapter_display_name,
              children: [
                {
                  sequential_id2: chapter_display_name
                  children: [...]
                }
                ...
              ]
            },
            ...
         ]
    **Example GET Response**
        [
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
    """

    queryset = Import.objects.all()
    lookup_field = 'uuid'
    lookup_url_kwarg = 'import_uuid'

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
        import_event = get_object_or_404(Import, uuid=self.kwargs['import_uuid'])
        staged_content = [
            staged_content_for_import.staged_content
            for staged_content_for_import in import_event.staged_content_for_import.all()
        ]

        return Response(self.get_structure_for_course_from_stage_content(staged_content))

    def get_structure_for_course_from_stage_content(self, staged_content) -> list[dict]:
        """
        Build course structure of the course from staged content.
        This method retrieves the staged content for the given course ID and constructs
        a hierarchical structure representing the course's content. The structure is built
        by parsing the OLX  fragments and mapping them to their respective usage keys.
        """
        parser = etree.XMLParser(strip_cdata=False)

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
