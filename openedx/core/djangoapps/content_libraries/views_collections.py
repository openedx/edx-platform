"""
Collections API Views
"""

from __future__ import annotations

from django.db.models import QuerySet
from django.utils.text import slugify
from django.db import transaction

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.status import HTTP_204_NO_CONTENT

from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import Collection

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.content_libraries.views import convert_exceptions
from openedx.core.djangoapps.content_libraries.serializers import (
    ContentLibraryCollectionSerializer,
    ContentLibraryCollectionComponentsUpdateSerializer,
    ContentLibraryCollectionUpdateSerializer,
)


class LibraryCollectionsView(ModelViewSet):
    """
    Views to get, create and update Library Collections.
    """

    serializer_class = ContentLibraryCollectionSerializer
    lookup_field = 'key'

    def __init__(self, *args, **kwargs) -> None:
        """
        Caches the ContentLibrary for the duration of the request.
        """
        super().__init__(*args, **kwargs)
        self._content_library: ContentLibrary | None = None

    def get_content_library(self) -> ContentLibrary:
        """
        Returns the requested ContentLibrary object, if access allows.
        """
        if self._content_library:
            return self._content_library

        lib_key_str = self.kwargs["lib_key_str"]
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        permission = (
            permissions.CAN_VIEW_THIS_CONTENT_LIBRARY
            if self.request.method in ['OPTIONS', 'GET']
            else permissions.CAN_EDIT_THIS_CONTENT_LIBRARY
        )

        self._content_library = api.require_permission_for_library_key(
            library_key,
            self.request.user,
            permission,
        )
        return self._content_library

    def get_queryset(self) -> QuerySet[Collection]:
        """
        Returns a queryset for the requested Collections, if access allows.

        This method may raise exceptions; these are handled by the @convert_exceptions wrapper on the views.
        """
        content_library = self.get_content_library()
        assert content_library.learning_package_id
        return authoring_api.get_collections(content_library.learning_package_id)

    def get_object(self) -> Collection:
        """
        Returns the requested Collections, if access allows.

        This method may raise exceptions; these are handled by the @convert_exceptions wrapper on the views.
        """
        collection = super().get_object()
        content_library = self.get_content_library()

        # Ensure the ContentLibrary and Collection share the same learning package
        if collection.learning_package_id != content_library.learning_package_id:
            raise api.ContentLibraryCollectionNotFound
        return collection

    @convert_exceptions
    def retrieve(self, request, *args, **kwargs) -> Response:
        """
        Retrieve the Content Library Collection
        """
        # View declared so we can wrap it in @convert_exceptions
        return super().retrieve(request, *args, **kwargs)

    @convert_exceptions
    def list(self, request, *args, **kwargs) -> Response:
        """
        List Collections that belong to Content Library
        """
        # View declared so we can wrap it in @convert_exceptions
        return super().list(request, *args, **kwargs)

    @convert_exceptions
    def create(self, request, *args, **kwargs) -> Response:
        """
        Create a Collection that belongs to a Content Library
        """
        content_library = self.get_content_library()
        create_serializer = ContentLibraryCollectionUpdateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)

        title = create_serializer.validated_data['title']
        key = slugify(title)

        attempt = 0
        collection = None
        while not collection:
            modified_key = key if attempt == 0 else key + '-' + str(attempt)
            try:
                # Add transaction here to avoid TransactionManagementError on retry
                with transaction.atomic():
                    collection = api.create_library_collection(
                        library_key=content_library.library_key,
                        content_library=content_library,
                        collection_key=modified_key,
                        title=title,
                        description=create_serializer.validated_data["description"],
                        created_by=request.user.id,
                    )
            except api.LibraryCollectionAlreadyExists:
                attempt += 1

        serializer = self.get_serializer(collection)

        return Response(serializer.data)

    @convert_exceptions
    def partial_update(self, request, *args, **kwargs) -> Response:
        """
        Update a Collection that belongs to a Content Library
        """
        content_library = self.get_content_library()
        collection_key = kwargs["key"]

        update_serializer = ContentLibraryCollectionUpdateSerializer(
            data=request.data, partial=True
        )
        update_serializer.is_valid(raise_exception=True)
        updated_collection = api.update_library_collection(
            library_key=content_library.library_key,
            collection_key=collection_key,
            content_library=content_library,
            **update_serializer.validated_data
        )
        serializer = self.get_serializer(updated_collection)

        return Response(serializer.data)

    @convert_exceptions
    def destroy(self, request, *args, **kwargs) -> Response:
        """
        Soft-deletes a Collection that belongs to a Content Library
        """
        collection = super().get_object()
        assert collection.learning_package_id
        authoring_api.delete_collection(
            collection.learning_package_id,
            collection.key,
            hard_delete=False,
        )
        return Response(None, status=HTTP_204_NO_CONTENT)

    @convert_exceptions
    @action(detail=True, methods=['post'], url_path='restore', url_name='collection-restore')
    def restore(self, request, *args, **kwargs) -> Response:
        """
        Restores a soft-deleted Collection that belongs to a Content Library
        """
        content_library = self.get_content_library()
        assert content_library.learning_package_id
        collection_key = kwargs["key"]
        authoring_api.restore_collection(
            content_library.learning_package_id,
            collection_key,
        )
        return Response(None, status=HTTP_204_NO_CONTENT)

    @convert_exceptions
    @action(detail=True, methods=['delete', 'patch'], url_path='components', url_name='components-update')
    def update_components(self, request, *args, **kwargs) -> Response:
        """
        Adds (PATCH) or removes (DELETE) Components to/from a Collection.

        Collection and Components must all be part of the given library/learning package.
        """
        content_library = self.get_content_library()
        collection_key = kwargs["key"]

        serializer = ContentLibraryCollectionComponentsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        usage_keys = serializer.validated_data["usage_keys"]
        api.update_library_collection_components(
            library_key=content_library.library_key,
            content_library=content_library,
            collection_key=collection_key,
            usage_keys=usage_keys,
            created_by=self.request.user.id,
            remove=(request.method == "DELETE"),
        )

        return Response({'count': len(usage_keys)})
