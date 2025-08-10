"""
API v0 views.
"""

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from user_tasks.models import UserTaskStatus
from user_tasks.views import StatusViewSet

from cms.djangoapps.modulestore_migrator.api import start_migration_to_library
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from .serializers import ModulestoreMigrationSerializer, StatusWithModulestoreMigrationSerializer


class ImportViewSet(StatusViewSet):
    """
    Import course content from modulestore into a content library.

    This viewset handles the import process, including creating the import task and
    retrieving the status of the import task. Meant to be used by admin users only.

    API Endpoints
    ------------
    POST /api/modulestore_migrator/v0/imports/
        Start the import process.

        Request body:
            {
                "source": "<source_course_key>",
                "target": "<target_library>",
                "composition_level": "<composition_level>",  # Optional, defaults to "component"
                "target_collection_slug": "<target_collection_slug>",  # Optional
                "replace_existing": "<boolean>"  # Optional, defaults to false
                "preserve_url_slugs": "<boolean>"  # Optional, defaults to true
            }

        Example request:
            {
                "source": "course-v1:edX+DemoX+2014_T1",
                "target": "library-v1:org1+lib_1",
                "composition_level": "unit",
                "replace_existing": true
                "preserve_url_slugs": true
            }

        Example response:
            {
                "name": migrate_from_modulestore",
                "state": "Succeeded",
                "state_text": "Succeeded",
                "completed_steps": 11,
                "total_steps": 11,
                "attempts": 1,
                "created": "2025-05-14T22:24:37.048539Z",
                "modified": "2025-05-14T22:24:59.128068Z",
                "artifacts": [],
                "modulestoremigration": {
                    "source": "course-v1:OpenedX+DemoX+DemoCourse",
                    "composition_level": "unit",
                    "replace_existing": true
                    "preserve_url_slugs": true
                }
            }

    GET /api/modulestore_migrator/v0/imports/<uuid>/
        Get the status of the import task.

        Example response:
            {
                "name": "migrate_from_modulestore",
                "state": "Importing staged files and resources",
                "state_text": "Importing staged content structure",
                "completed_steps": 6,
                "total_steps": 11,
                "attempts": 1,
                "created": "2025-05-14T22:24:37.048539Z",
                "modified": "2025-05-14T22:24:59.128068Z",
                "artifacts": [],
                "modulestoremigration": {
                    "source": "course-v1:OpenedX+DemoX+DemoCourse2",
                    "composition_level": "component",
                    "replace_existing": false
                    "preserve_url_slugs": false
                }
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
        Override the default queryset to filter by the import event and user.
        """
        return StatusViewSet.queryset.filter(modulestoremigration__isnull=False, user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Handle the import task creation.
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
            replace_existing=validated_data['replace_existing'],
            preserve_url_slugs=validated_data['preserve_url_slugs'],
            forward_source_to_target=False,  # @@TODO - Set to False for now. Explain this better.
        )

        task_status = UserTaskStatus.objects.get(task_id=task.id)
        serializer = self.get_serializer(task_status)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
