"""
Collections API Views
"""

from __future__ import annotations

from django.http import Http404

from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.status import HTTP_405_METHOD_NOT_ALLOWED

from opaque_keys.edx.locator import LibraryLocatorV2

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.serializers import (
    ContentLibraryCollectionSerializer,
    ContentLibraryCollectionCreateOrUpdateSerializer,
)

from openedx_learning.api.authoring_models import Collection
from openedx_learning.api import authoring as authoring_api


class LibraryCollectionsView(ModelViewSet):
    """
    Views to get, create and update Library Collections.
    """

    serializer_class = ContentLibraryCollectionSerializer

    def _verify_and_fetch_library_collection(self, library_key, collection_id, user, permission) -> Collection | None:
        """
        Verify that the collection belongs to the library and the user has the correct permissions
        """
        try:
            library_obj = api.require_permission_for_library_key(library_key, user, permission)
        except api.ContentLibraryNotFound:
            raise Http404

        collection = None
        if library_obj.learning_package_id:
            collection = authoring_api.get_learning_package_collections(
                library_obj.learning_package_id
            ).filter(id=collection_id).first()
        return collection

    def retrieve(self, request, lib_key_str, pk=None):
        """
        Retrieve the Content Library Collection
        """
        library_key = LibraryLocatorV2.from_string(lib_key_str)

        # Check if user has permissions to view this collection by checking if
        # user has permission to view the Content Library it belongs to
        collection = self._verify_and_fetch_library_collection(
            library_key, pk, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY
        )

        if not collection:
            raise Http404

        serializer = self.get_serializer(collection)
        return Response(serializer.data)

    def list(self, request, lib_key_str):
        """
        List Collections that belong to Content Library
        """
        # Check if user has permissions to view collections by checking if user
        # has permission to view the Content Library they belong to
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        try:
            content_library = api.require_permission_for_library_key(
                library_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY
            )
        except api.ContentLibraryNotFound:
            raise Http404

        collections = authoring_api.get_learning_package_collections(content_library.learning_package.id)
        serializer = self.get_serializer(collections, many=True)
        return Response(serializer.data)

    def create(self, request, lib_key_str):
        """
        Create a Collection that belongs to a Content Library
        """
        # Check if user has permissions to create a collection in the Content Library
        # by checking if user has permission to edit the Content Library
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        try:
            content_library = api.require_permission_for_library_key(
                library_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY
            )
        except api.ContentLibraryNotFound:
            raise Http404

        create_serializer = ContentLibraryCollectionCreateOrUpdateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        collection = authoring_api.create_collection(
            content_library.learning_package.id,
            create_serializer.validated_data["title"],
            request.user.id,
            create_serializer.validated_data["description"]
        )
        serializer = self.get_serializer(collection)
        return Response(serializer.data)

    def partial_update(self, request, lib_key_str, pk=None):
        """
        Update a Collection that belongs to a Content Library
        """
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        # Check if user has permissions to update a collection in the Content Library
        # by checking if user has permission to edit the Content Library
        collection = self._verify_and_fetch_library_collection(
            library_key, pk, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY
        )

        if not collection:
            raise Http404

        update_serializer = ContentLibraryCollectionCreateOrUpdateSerializer(
            collection, data=request.data, partial=True
        )
        update_serializer.is_valid(raise_exception=True)
        updated_collection = authoring_api.update_collection(pk, **update_serializer.validated_data)
        serializer = self.get_serializer(updated_collection)
        return Response(serializer.data)

    def destroy(self, request, lib_key_str, pk=None):
        """
        Deletes a Collection that belongs to a Content Library

        Note: (currently not allowed)
        """
        return Response(None, status=HTTP_405_METHOD_NOT_ALLOWED)
