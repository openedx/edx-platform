"""
Collections API Views
"""

from __future__ import annotations

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.status import HTTP_405_METHOD_NOT_ALLOWED

from opaque_keys.edx.locator import LibraryLocatorV2

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.content_libraries.views import convert_exceptions
from openedx.core.djangoapps.content_libraries.serializers import (
    ContentLibraryCollectionSerializer,
    ContentLibraryCollectionComponentsUpdateSerializer,
    ContentLibraryCollectionCreateOrUpdateSerializer,
)

from openedx_learning.api.authoring_models import Collection
from openedx_learning.api import authoring as authoring_api


class LibraryCollectionsView(ModelViewSet):
    """
    Views to get, create and update Library Collections.
    """

    serializer_class = ContentLibraryCollectionSerializer

    def _verify_and_fetch_library_collection(
        self,
        library_key,
        collection_id,
        user,
        permission,
    ) -> tuple[ContentLibrary, Collection]:
        """
        Verify that the collection belongs to the library and the user has the correct permissions.

        This method may raise exceptions; these are handled by the @convert_exceptions wrapper on the views.
        """
        library_obj = api.require_permission_for_library_key(library_key, user, permission)
        collection = None
        if library_obj.learning_package_id:
            collection = authoring_api.get_collections(
                library_obj.learning_package_id
            ).filter(id=collection_id).first()
        if not collection:
            raise api.ContentLibraryCollectionNotFound
        return library_obj, collection

    @convert_exceptions
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve the Content Library Collection
        """
        lib_key_str = kwargs.pop("lib_key_str")
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        pk = kwargs.pop("pk")

        # Check if user has permissions to view this collection by checking if
        # user has permission to view the Content Library it belongs to
        _, collection = self._verify_and_fetch_library_collection(
            library_key, pk, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY
        )

        serializer = self.get_serializer(collection)
        return Response(serializer.data)

    @convert_exceptions
    def list(self, request, *args, **kwargs):
        """
        List Collections that belong to Content Library
        """
        lib_key_str = kwargs.pop("lib_key_str")
        library_key = LibraryLocatorV2.from_string(lib_key_str)

        # Check if user has permissions to view collections by checking if user
        # has permission to view the Content Library they belong to
        content_library = api.require_permission_for_library_key(
            library_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY
        )

        collections = authoring_api.get_collections(content_library.learning_package.id)
        serializer = self.get_serializer(collections, many=True)
        return Response(serializer.data)

    @convert_exceptions
    def create(self, request, *args, **kwargs):
        """
        Create a Collection that belongs to a Content Library
        """
        lib_key_str = kwargs.pop("lib_key_str")
        library_key = LibraryLocatorV2.from_string(lib_key_str)

        # Check if user has permissions to create a collection in the Content Library
        # by checking if user has permission to edit the Content Library
        content_library = api.require_permission_for_library_key(
            library_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY
        )

        create_serializer = ContentLibraryCollectionCreateOrUpdateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        collection = api.create_library_collection(
            library_key=library_key,
            content_library=content_library,
            title=create_serializer.validated_data["title"],
            description=create_serializer.validated_data["description"],
            created_by=request.user.id,
        )
        serializer = self.get_serializer(collection)

        return Response(serializer.data)

    @convert_exceptions
    def partial_update(self, request, *args, **kwargs):
        """
        Update a Collection that belongs to a Content Library
        """
        lib_key_str = kwargs.pop('lib_key_str')
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        pk = kwargs.pop('pk')

        # Check if user has permissions to update a collection in the Content Library
        # by checking if user has permission to edit the Content Library
        self._verify_and_fetch_library_collection(
            library_key, pk, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY
        )

        update_serializer = ContentLibraryCollectionCreateOrUpdateSerializer(
            data=request.data, partial=True
        )
        update_serializer.is_valid(raise_exception=True)
        updated_collection = api.update_library_collection(
            library_key=library_key,
            collection_id=pk,
            **update_serializer.validated_data
        )
        serializer = self.get_serializer(updated_collection)

        return Response(serializer.data)

    @convert_exceptions
    def destroy(self, request, *args, **kwargs):
        """
        Deletes a Collection that belongs to a Content Library

        Note: (currently not allowed)
        """
        # TODO: Implement the deletion logic and emit event signal

        return Response(None, status=HTTP_405_METHOD_NOT_ALLOWED)

    @convert_exceptions
    @action(detail=True, methods=['delete', 'patch'], url_path='components', url_name='components-update')
    def update_components(self, request, lib_key_str, pk):
        """
        Adds (PATCH) or removes (DELETE) Components to/from a Collection.

        Collection and Components must all be part of the given library/learning package.
        """
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        library_obj, _ = self._verify_and_fetch_library_collection(
            library_key, pk, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY
        )

        serializer = ContentLibraryCollectionComponentsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usage_keys = serializer.validated_data["usage_keys"]
        api.update_library_collection_components(
            library_key=library_key,
            content_library=library_obj,
            collection_id=pk,
            usage_keys=usage_keys,
            created_by=self.request.user.id,
            remove=(request.method == "DELETE"),
        )

        return Response({'count': len(usage_keys)})
