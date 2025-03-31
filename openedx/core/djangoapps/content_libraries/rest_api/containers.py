"""
REST API views for containers (sections, subsections, units) in content libraries
"""
from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.db.transaction import non_atomic_requests
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema

from opaque_keys.edx.locator import LibraryLocatorV2, LibraryContainerLocator
from openedx_learning.api import authoring as authoring_api
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.lib.api.view_utils import view_auth_classes
from . import serializers
from .utils import convert_exceptions

User = get_user_model()
log = logging.getLogger(__name__)


@method_decorator(non_atomic_requests, name="dispatch")
@view_auth_classes()
class LibraryContainersView(GenericAPIView):
    """
    Views to work with Containers in a specific content library.
    """
    serializer_class = serializers.LibraryContainerMetadataSerializer

    @convert_exceptions
    @swagger_auto_schema(
        request_body=serializers.LibraryContainerMetadataSerializer,
        responses={200: serializers.LibraryContainerMetadataSerializer}
    )
    def post(self, request, lib_key_str):
        """
        Create a new Container in this content library
        """
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(library_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        serializer = serializers.LibraryContainerMetadataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        container_type = serializer.validated_data['container_type']
        container = api.create_container(
            library_key,
            container_type,
            title=serializer.validated_data['display_name'],
            slug=serializer.validated_data.get('slug'),
            user_id=request.user.id,
        )

        return Response(serializers.LibraryContainerMetadataSerializer(container).data)


@method_decorator(non_atomic_requests, name="dispatch")
@view_auth_classes()
class LibraryContainerView(GenericAPIView):
    """
    View to retrieve or update data about a specific container (a section, subsection, or unit)
    """
    serializer_class = serializers.LibraryContainerMetadataSerializer

    @convert_exceptions
    @swagger_auto_schema(
        responses={200: serializers.LibraryContainerMetadataSerializer}
    )
    def get(self, request, container_key: LibraryContainerLocator):
        """
        Get information about a container
        """
        api.require_permission_for_library_key(
            container_key.library_key,
            request.user,
            permissions.CAN_VIEW_THIS_CONTENT_LIBRARY,
        )
        container = api.get_container(container_key)
        return Response(serializers.LibraryContainerMetadataSerializer(container).data)

    @convert_exceptions
    @swagger_auto_schema(
        request_body=serializers.LibraryContainerUpdateSerializer,
        responses={200: serializers.LibraryContainerMetadataSerializer}
    )
    def patch(self, request, container_key: LibraryContainerLocator):
        """
        Update a Container.
        """
        api.require_permission_for_library_key(
            container_key.library_key,
            request.user,
            permissions.CAN_EDIT_THIS_CONTENT_LIBRARY,
        )
        serializer = serializers.LibraryContainerUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        container = api.update_container(
            container_key,
            display_name=serializer.validated_data['display_name'],
            user_id=request.user.id,
        )

        return Response(serializers.LibraryContainerMetadataSerializer(container).data)

    @convert_exceptions
    def delete(self, request, container_key: LibraryContainerLocator):
        """
        Delete a Container (soft delete).
        """
        api.require_permission_for_library_key(
            container_key.library_key,
            request.user,
            permissions.CAN_EDIT_THIS_CONTENT_LIBRARY,
        )

        api.delete_container(
            container_key,
        )

        return Response({}, status=HTTP_204_NO_CONTENT)


@method_decorator(non_atomic_requests, name="dispatch")
@view_auth_classes()
class LibraryContainerChildrenView(GenericAPIView):
    """
    View to get or update children of specific container (a section, subsection, or unit)
    """
    serializer_class = serializers.LibraryXBlockMetadataSerializer

    @convert_exceptions
    @swagger_auto_schema(
        responses={200: list[serializers.LibraryXBlockMetadataSerializer]}
    )
    def get(self, request, container_key: LibraryContainerLocator):
        """
        Get children components of given container
        Example:
        GET /api/libraries/v2/containers/<container_key>/children/
        Result:
        [
            {
                'block_type': 'problem',
                'can_stand_alone': True,
                'collections': [],
                'created': '2025-03-21T13:53:55Z',
                'def_key': None,
                'display_name': 'Blank Problem',
                'has_unpublished_changes': True,
                'id': 'lb:CL-TEST:containers:problem:Problem1',
                'last_draft_created': '2025-03-21T13:53:55Z',
                'last_draft_created_by': 'Bob',
                'last_published': None,
                'modified': '2025-03-21T13:53:55Z',
                'published_by': None,
            },
            {
                'block_type': 'html',
                'can_stand_alone': False,
                'collections': [],
                'created': '2025-03-21T13:53:55Z',
                'def_key': None,
                'display_name': 'Text',
                'has_unpublished_changes': True,
                'id': 'lb:CL-TEST:containers:html:Html1',
                'last_draft_created': '2025-03-21T13:53:55Z',
                'last_draft_created_by': 'Bob',
                'last_published': None,
                'modified': '2025-03-21T13:53:55Z',
                'published_by': None,
            }
        ]
        """
        published = request.GET.get('published', False)
        api.require_permission_for_library_key(
            container_key.library_key,
            request.user,
            permissions.CAN_VIEW_THIS_CONTENT_LIBRARY,
        )
        child_entities = api.get_container_children(container_key, published)
        if container_key.container_type == api.ContainerType.Unit.value:
            data = serializers.LibraryXBlockMetadataSerializer(child_entities, many=True).data
        else:
            data = serializers.LibraryContainerMetadataSerializer(child_entities, many=True).data
        return Response(data)

    def _update_component_children(
        self,
        request,
        container_key: LibraryContainerLocator,
        action: authoring_api.ChildrenEntitiesAction,
    ):
        """
        Helper function to update children in container.
        """
        api.require_permission_for_library_key(
            container_key.library_key,
            request.user,
            permissions.CAN_EDIT_THIS_CONTENT_LIBRARY,
        )
        serializer = serializers.ContentLibraryComponentKeysSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Only components under units are supported for now.
        assert container_key.container_type == api.ContainerType.Unit.value

        container = api.update_container_children(
            container_key,
            children_ids=serializer.validated_data["usage_keys"],
            user_id=request.user.id,
            entities_action=action,
        )
        return Response(serializers.LibraryContainerMetadataSerializer(container).data)

    @convert_exceptions
    @swagger_auto_schema(
        request_body=serializers.ContentLibraryComponentKeysSerializer,
        responses={200: serializers.LibraryContainerMetadataSerializer}
    )
    def post(self, request, container_key: LibraryContainerLocator):
        """
        Add components to unit
        Example:
        POST /api/libraries/v2/containers/<container_key>/children/
        Request body:
        {"usage_keys": ['lb:CL-TEST:containers:problem:Problem1', 'lb:CL-TEST:containers:html:Html1']}
        """
        return self._update_component_children(
            request,
            container_key,
            action=authoring_api.ChildrenEntitiesAction.APPEND,
        )

    @convert_exceptions
    @swagger_auto_schema(
        request_body=serializers.ContentLibraryComponentKeysSerializer,
        responses={200: serializers.LibraryContainerMetadataSerializer}
    )
    def delete(self, request, container_key: LibraryContainerLocator):
        """
        Remove components from unit
        Example:
        DELETE /api/libraries/v2/containers/<container_key>/children/
        Request body:
        {"usage_keys": ['lb:CL-TEST:containers:problem:Problem1', 'lb:CL-TEST:containers:html:Html1']}
        """
        return self._update_component_children(
            request,
            container_key,
            action=authoring_api.ChildrenEntitiesAction.REMOVE,
        )

    @convert_exceptions
    @swagger_auto_schema(
        request_body=serializers.ContentLibraryComponentKeysSerializer,
        responses={200: serializers.LibraryContainerMetadataSerializer}
    )
    def patch(self, request, container_key: LibraryContainerLocator):
        """
        Replace components in unit, can be used to reorder components as well.
        Example:
        PATCH /api/libraries/v2/containers/<container_key>/children/
        Request body:
        {"usage_keys": ['lb:CL-TEST:containers:problem:Problem1', 'lb:CL-TEST:containers:html:Html1']}
        """
        return self._update_component_children(
            request,
            container_key,
            action=authoring_api.ChildrenEntitiesAction.REPLACE,
        )
