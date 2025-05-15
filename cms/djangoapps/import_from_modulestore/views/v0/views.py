"""
API v0 views.
"""

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.locator import LibraryLocatorV2
from rest_framework.permissions import IsAdminUser
from user_tasks.models import UserTaskStatus
from user_tasks.views import StatusViewSet

from cms.djangoapps.import_from_modulestore.api import import_to_library
from cms.djangoapps.import_from_modulestore.views.v0.serializers import ImportSerializer, StatusWithImportSerializer
from openedx.core.djangoapps.content_libraries.api import ContentLibrary
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser


class ImportViewSet(StatusViewSet):
    """
    Import course content from modulestore into a content library.

    This viewset handles the import process, including creating the import task and
    retrieving the status of the import task. Meant to be used by admin users only.

    API Endpoints
    ------------
    POST /api/import_from_modulestore/v0/imports/
        Start the import process.

        Request body:
            {
                "source_key": "<source_course_key>",
                "target": "<target_library>",
                "usage_keys_string": "<comma_separated_usage_keys>",
                "composition_level": "<composition_level>",
                "override": "<boolean>"
            }

        Example request:
            {
                "source_key": "course-v1:edX+DemoX+2014_T1",
                "target": "library-v1:org1+lib_1",
                "usage_keys_string": "block-v1:edX+DemoX+2014_T1+type@sequential+block@chapter_1",
                "composition_level": "component",
                "override": true
            }

        Example response:
            {
                "name": "Import course to library (library_id=6, import_id=50)",
                "state": "Succeeded",
                "state_text": "Succeeded",
                "completed_steps": 2,
                "total_steps": 2,
                "attempts": 1,
                "created": "2025-05-14T22:24:37.048539Z",
                "modified": "2025-05-14T22:24:59.128068Z",
                "artifacts": [],
                "import_event": {
                    "source_key": "course-v1:OpenedX+DemoX+DemoCourse",
                    "composition_level": "component",
                    "override": true
                }
            }

    GET /api/import_from_modulestore/v0/imports/<uuid>/
        Get the status of the import task.

        Example response:
            {
                "name": "Import course to library (library_id=4, import_id=69)",
                "state": "Importing staged content",
                "state_text": "Importing staged content",
                "completed_steps": 1,
                "total_steps": 2,
                "attempts": 1,
                "created": "2025-05-14T22:24:37.048539Z",
                "modified": "2025-05-14T22:24:59.128068Z",
                "artifacts": [],
                "import_event": {
                    "source_key": "course-v1:OpenedX+DemoX+DemoCourse2",
                    "composition_level": "component",
                    "override": false
                }
            }
    """

    permission_classes = (IsAdminUser,)
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    serializer_class = StatusWithImportSerializer

    def get_queryset(self):
        """
        Override the default queryset to filter by the import event and user.
        """
        return StatusViewSet.queryset.filter(import_event__isnull=False, user_id=self.request.user.pk)

    def create(self, request, *args, **kwargs):
        """
        Handle the import task creation.
        """

        serializer_data = ImportSerializer(data=request.data)
        serializer_data.is_valid(raise_exception=True)
        validated_data = serializer_data.validated_data

        library_key = LibraryLocatorV2.from_string(validated_data['target'])
        learning_package_id = ContentLibrary.objects.get(
            org__short_name=library_key.org, slug=library_key.slug
        ).learning_package_id

        _, task = import_to_library(
            source_key=validated_data['source_key'],
            usage_ids=validated_data['usage_keys_string'],
            target_learning_package_id=learning_package_id,
            user_id=request.user.pk,
            composition_level=validated_data['composition_level'],
            override=validated_data['override'],
        )
        return UserTaskStatus.objects.get(uuid=task.id)
