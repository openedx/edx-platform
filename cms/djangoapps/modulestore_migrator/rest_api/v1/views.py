"""
API v1 views.
"""
import logging

import edx_api_doc_tools as apidocs
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from user_tasks.models import UserTaskStatus
from user_tasks.views import StatusViewSet

from cms.djangoapps.modulestore_migrator.api import (
    start_migration_to_library,
    start_bulk_migration_to_library,
    get_all_migrations_info,
)
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from .serializers import (
    StatusWithModulestoreMigrationSerializer,
    ModulestoreMigrationSerializer,
    BulkModulestoreMigrationSerializer,
    MigrationInfoResponseSerializer,
)


log = logging.getLogger(__name__)


class MigrationViewSet(StatusViewSet):
    """
    Import course content or legacy library content from modulestore into a content library.

    This viewset handles the import process, including creating the import task and
    retrieving the status of the import task. Meant to be used by admin users only.

    API Endpoints
    ------------
    POST /api/modulestore_migrator/v1/migrations/
        Start the import process.

        Request body:
            {
                "source": "<source_course_key>",
                "target": "<target_library>",
                "composition_level": "<composition_level>",  # Optional, defaults to "component"
                "target_collection_slug": "<target_collection_slug>",  # Optional
                "repeat_handling_strategy": "<repeat_handling_strategy>"  # Optional, defaults to Skip
                "preserve_url_slugs": "<boolean>"  # Optional, defaults to true
            }

        Example request:
            {
                "source": "course-v1:edX+DemoX+2014_T1",
                "target": "library-v1:org1+lib_1",
                "composition_level": "unit",
                "repeat_handling_strategy": "update",
                "preserve_url_slugs": true
            }

        Example response:
            {
                "state": "Succeeded",
                "state_text": "Succeeded",  # Translation into the current language of the current state
                "completed_steps": 11,
                "total_steps": 11,
                "attempts": 1,
                "created": "2025-05-14T22:24:37.048539Z",
                "modified": "2025-05-14T22:24:59.128068Z",
                "artifacts": [],
                "uuid": "3de23e5d-fd34-4a6f-bf02-b183374120f0",
                "parameters": {
                    "source": "course-v1:OpenedX+DemoX+DemoCourse",
                    "composition_level": "unit",
                    "repeat_handling_strategy": "update",
                    "preserve_url_slugs": true
                }
            }

    GET /api/modulestore_migrator/v1/migrations/<uuid>/
        Get the status of the import task.

        Example response:
            {
                "state": "Importing staged content structure",
                "state_text": "Importing staged content structure",
                "completed_steps": 6,
                "total_steps": 11,
                "attempts": 1,
                "created": "2025-05-14T22:24:37.048539Z",
                "modified": "2025-05-14T22:24:59.128068Z",
                "artifacts": [],
                "uuid": "3de23e5d-fd34-4a6f-bf02-b183374120f0",
                "parameters": [
                    {
                        "source": "course-v1:OpenedX+DemoX+DemoCourse2",
                        "composition_level": "component",
                        "repeat_handling_strategy": "skip",
                        "preserve_url_slugs": false
                    }
                ]
            }
    """

    permission_classes = (IsAdminUser,)
    authentication_classes = (
        BearerAuthenticationAllowInactiveUser,
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    serializer_class = StatusWithModulestoreMigrationSerializer

    def get_queryset(self):
        """
        Override the default queryset to filter by the migration event and user.
        """
        return StatusViewSet.queryset.filter(migrations__isnull=False, user=self.request.user).distinct()

    @apidocs.schema(
        body=ModulestoreMigrationSerializer,
        responses={
            201: StatusWithModulestoreMigrationSerializer,
            401: "The requester is not authenticated.",
        },
        summary="Start a modulestore to content library migration",
        description=(
            "Create a migration task to import course or legacy library content into "
            "a content library.\n\n"
            "**Request example**:\n\n"
            "```json\n"
            "{\n"
            '  "source": "course-v1:edX+DemoX+2014_T1",\n'
            '  "target": "library-v1:org1+lib_1",\n'
            '  "composition_level": "unit",\n'
            '  "repeat_handling_strategy": "update",\n'
            '  "preserve_url_slugs": true\n'
            "}\n"
            "```"
        ),
    )
    def create(self, request, *args, **kwargs):
        """
        Handle the migration task creation.
        """

        serializer_data = ModulestoreMigrationSerializer(data=request.data)
        serializer_data.is_valid(raise_exception=True)
        validated_data = serializer_data.validated_data

        task = start_migration_to_library(
            user=request.user,
            source_key=validated_data['source'],
            target_library_key=validated_data['target'],
            target_collection_slug=validated_data['target_collection_slug'],
            composition_level=validated_data['composition_level'],
            repeat_handling_strategy=validated_data['repeat_handling_strategy'],
            preserve_url_slugs=validated_data['preserve_url_slugs'],
            forward_source_to_target=validated_data['forward_source_to_target'],
        )

        task_status = UserTaskStatus.objects.get(task_id=task.id)
        serializer = self.get_serializer(task_status)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BulkMigrationViewSet(StatusViewSet):
    """
    Import content of a list of courses or legacy libraries from modulestore into a content library.

    This viewset handles the import process, including creating the import task and
    retrieving the status of the import task. Meant to be used by admin users only.

    API Endpoints
    ------------
    POST /api/modulestore_migrator/v1/bulk-migration/
        Start the bulk import process.

        Request body:
            {
                "sources": ["<source_course_key_1>", "<source_course_key_2>"],
                "target": "<target_library>",
                "composition_level": "<composition_level>",  # Optional, defaults to "component"
                "target_collection_slugs": ["<target_collection_slug_1>", "<target_collection_slug_1>"],  # Optional
                "create_collections": "<boolean>"  # Optional, defaults to false
                "repeat_handling_strategy": "<repeat_handling_strategy>"  # Optional, defaults to Skip
                "preserve_url_slugs": "<boolean>"  # Optional, defaults to true
            }

        Example request:
            {
                "sources": ["course-v1:edX+DemoX+2014_T1", "course-v1:edX+DemoX+2014_T2"],
                "target": "library-v1:org1+lib_1",
                "composition_level": "unit",
                "repeat_handling_strategy": "update",
                "preserve_url_slugs": true,
                "create_collections": true
            }

        Example response:
            {
                "state": "Succeeded",
                "state_text": "Succeeded",  # Translation into the current language of the current state
                "completed_steps": 11,
                "total_steps": 11,
                "attempts": 1,
                "created": "2025-05-14T22:24:37.048539Z",
                "modified": "2025-05-14T22:24:59.128068Z",
                "artifacts": [],
                "uuid": "3de23e5d-fd34-4a6f-bf02-b183374120f0",
                "parameters": [
                    {
                        "source": "course-v1:edX+DemoX+2014_T1",
                        "composition_level": "unit",
                        "repeat_handling_strategy": "update",
                        "preserve_url_slugs": true
                    },
                    {
                        "source": "course-v1:edX+DemoX+2014_T2",
                        "composition_level": "unit",
                        "repeat_handling_strategy": "update",
                        "preserve_url_slugs": true
                    },
                ]
            }

    GET Not Alowed
    """

    permission_classes = (IsAdminUser,)
    authentication_classes = (
        BearerAuthenticationAllowInactiveUser,
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    serializer_class = StatusWithModulestoreMigrationSerializer
    http_method_names = ["post"]

    @apidocs.schema(
        body=BulkModulestoreMigrationSerializer,
        responses={
            201: StatusWithModulestoreMigrationSerializer,
            401: "The requester is not authenticated.",
        },
        summary="Start a bulk modulestore to content library migration",
        description=(
            "Create a migration task to import multiple courses or legacy libraries "
            "into a single content library.\n\n"
            "**Request example**:\n\n"
            "```json\n"
            "{\n"
            '  "sources": ["course-v1:edX+DemoX+2014_T1", "course-v1:edX+DemoX+2014_T2"],\n'
            '  "target": "library-v1:org1+lib_1",\n'
            '  "composition_level": "unit",\n'
            '  "repeat_handling_strategy": "update",\n'
            '  "preserve_url_slugs": true,\n'
            '  "create_collections": true\n'
            "}\n"
            "```"
        ),
    )
    def create(self, request, *args, **kwargs):
        """
        Handle the bulk migration task creation.
        """
        serializer_data = BulkModulestoreMigrationSerializer(data=request.data)
        serializer_data.is_valid(raise_exception=True)
        validated_data = serializer_data.validated_data

        task = start_bulk_migration_to_library(
            user=request.user,
            source_key_list=validated_data['sources'],
            target_library_key=validated_data['target'],
            target_collection_slug_list=validated_data['target_collection_slug_list'],
            create_collections=validated_data['create_collections'],
            composition_level=validated_data['composition_level'],
            repeat_handling_strategy=validated_data['repeat_handling_strategy'],
            preserve_url_slugs=validated_data['preserve_url_slugs'],
            forward_source_to_target=validated_data['forward_source_to_target'],
        )

        task_status = UserTaskStatus.objects.get(task_id=task.id)
        serializer = self.get_serializer(task_status)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MigrationInfoViewSet(APIView):
    """
    Retrieve migration information for a list of source courses or libraries.

    It returns the target library information associated with each successfully migrated source.

    API Endpoints
    -------------
    GET /api/modulestore_migrator/v1/migration-info/
        Retrieve migration details for one or more sources.

        Query parameters:
            source_keys (list[str]): List of course or library keys to check.
                Example: ?source_keys=course-v1:edX+DemoX+2024_T1&source_keys=library-v1:orgX+lib_2

        Example request:
            GET /api/modulestore_migrator/v1/migration-info/?source_keys=course-v1:edX+DemoX+2024_T1

        Example response:
            {
                "course-v1:edX+DemoX+2024_T1": [
                    {
                        "target_key": "library-v1:orgX+lib_2",
                        "target_title": "Demo Library",
                        "target_collection_key": "col-v2:1234abcd",
                        "target_collection_title": "Default Collection",
                        "source_key": "course-v1:edX+DemoX+2024_T1"
                    }
                ],
                "library-v1:orgX+lib_2": [
                    {
                        "target_key": "library-v1:orgX+lib_2",
                        "target_title": "Demo Library",
                        "target_collection_key": "col-v2:1234abcd",
                        "target_collection_title": "Default Collection",
                        "source_key": "course-v1:edX+DemoX+2024_T1"
                    },
                    {
                        "target_key": "library-v1:orgX+lib_2",
                        "target_title": "Demo Library",
                        "target_collection_key": "col-v2:1234abcd",
                        "target_collection_title": "Default Collection",
                        "source_key": "course-v1:edX+DemoX+2024_T1"
                    }
                ]
            }
    """

    permission_classes = (IsAdminUser,)
    authentication_classes = (
        BearerAuthenticationAllowInactiveUser,
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "source_keys",
                apidocs.ParameterLocation.QUERY,
                description="List of source keys to consult",
            ),
        ],
        responses={
            200: MigrationInfoResponseSerializer,
            400: "Missing required parameter: source_keys",
            401: "The requester is not authenticated.",
        },
    )
    def get(self, request):
        """
        Handle the migration info `GET` request
        """
        source_keys = request.query_params.getlist("source_keys")

        if not source_keys:
            return Response(
                {"detail": "Missing required parameter: source_keys"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = get_all_migrations_info(source_keys)
        serializer = MigrationInfoResponseSerializer(data)
        return Response(serializer.data)
