"""
REST API views for containers (sections, subsections, units) in content libraries
"""
from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.db.transaction import non_atomic_requests
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema

from opaque_keys.edx.locator import LibraryLocatorV2, LibraryContainerLocator
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
