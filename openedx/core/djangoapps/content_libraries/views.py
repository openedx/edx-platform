"""
REST API for Blockstore-based content libraries
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from functools import wraps
import logging

from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from organizations.models import Organization
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.lib.api.view_utils import view_auth_classes
from . import api
from .serializers import (
    ContentLibraryMetadataSerializer,
    ContentLibraryUpdateSerializer,
    LibraryXBlockCreationSerializer,
    LibraryXBlockMetadataSerializer,
    LibraryXBlockTypeSerializer,
    LibraryXBlockOlxSerializer,
    LibraryXBlockStaticFileSerializer,
    LibraryXBlockStaticFilesSerializer,
)

log = logging.getLogger(__name__)


def convert_exceptions(fn):
    """
    Catch any Content Library API exceptions that occur and convert them to
    DRF exceptions so DRF will return an appropriate HTTP response
    """

    @wraps(fn)
    def wrapped_fn(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except api.ContentLibraryNotFound:
            log.exception("Content library not found")
            raise NotFound
        except api.ContentLibraryBlockNotFound:
            log.exception("XBlock not found in content library")
            raise NotFound
        except api.LibraryBlockAlreadyExists as exc:
            log.exception(exc.message)
            raise ValidationError(exc.message)
        except api.InvalidNameError as exc:
            log.exception(exc.message)
            raise ValidationError(exc.message)
    return wrapped_fn


@view_auth_classes()
class LibraryRootView(APIView):
    """
    Views to list, search for, and create content libraries.
    """

    def get(self, request):
        """
        Return a list of all content libraries. This is a temporary view for
        development.
        """
        result = api.list_libraries()
        return Response(ContentLibraryMetadataSerializer(result, many=True).data)

    def post(self, request):
        """
        Create a new content library.
        """
        serializer = ContentLibraryMetadataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        # Get the organization short_name out of the "key.org" pseudo-field that the serializer added:
        org_name = data["key"]["org"]
        # Move "slug" out of the "key.slug" pseudo-field that the serializer added:
        data["slug"] = data.pop("key")["slug"]
        try:
            org = Organization.objects.get(short_name=org_name)
        except Organization.DoesNotExist:
            raise ValidationError(detail={"org": "No such organization '{}' found.".format(org_name)})
        try:
            result = api.create_library(org=org, **data)
        except api.LibraryAlreadyExists:
            raise ValidationError(detail={"slug": "A library with that ID already exists."})
        # Grant the current user admin permissions on the library:
        api.set_library_user_permissions(result.key, request.user, api.AccessLevel.ADMIN_LEVEL)
        return Response(ContentLibraryMetadataSerializer(result).data)


@view_auth_classes()
class LibraryDetailsView(APIView):
    """
    Views to work with a specific content library
    """
    @convert_exceptions
    def get(self, request, lib_key_str):
        """
        Get a specific content library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        result = api.get_library(key)
        return Response(ContentLibraryMetadataSerializer(result).data)

    @convert_exceptions
    def patch(self, request, lib_key_str):
        """
        Update a content library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        serializer = ContentLibraryUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        api.update_library(key, **serializer.validated_data)
        result = api.get_library(key)
        return Response(ContentLibraryMetadataSerializer(result).data)

    @convert_exceptions
    def delete(self, request, lib_key_str):  # pylint: disable=unused-argument
        """
        Delete a content library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.delete_library(key)
        return Response({})


@view_auth_classes()
class LibraryBlockTypesView(APIView):
    """
    View to get the list of XBlock types that can be added to this library
    """
    @convert_exceptions
    def get(self, request, lib_key_str):
        """
        Get the list of XBlock types that can be added to this library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        result = api.get_allowed_block_types(key)
        return Response(LibraryXBlockTypeSerializer(result, many=True).data)


@view_auth_classes()
class LibraryCommitView(APIView):
    """
    Commit/publish or revert all of the draft changes made to the library.
    """
    @convert_exceptions
    def post(self, request, lib_key_str):
        """
        Commit the draft changes made to the specified block and its
        descendants.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.publish_changes(key)
        return Response({})

    @convert_exceptions
    def delete(self, request, lib_key_str):  # pylint: disable=unused-argument
        """
        Revert the draft changes made to the specified block and its
        descendants. Restore it to the last published version
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.revert_changes(key)
        return Response({})


@view_auth_classes()
class LibraryBlocksView(APIView):
    """
    Views to work with XBlocks in a specific content library.
    """
    @convert_exceptions
    def get(self, request, lib_key_str):
        """
        Get the list of all top-level blocks in this content library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        result = api.get_library_blocks(key)
        return Response(LibraryXBlockMetadataSerializer(result, many=True).data)

    @convert_exceptions
    def post(self, request, lib_key_str):
        """
        Add a new XBlock to this content library
        """
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        serializer = LibraryXBlockCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        parent_block_usage_str = serializer.validated_data.pop("parent_block", None)
        if parent_block_usage_str:
            # Add this as a child of an existing block:
            parent_block_usage = LibraryUsageLocatorV2.from_string(parent_block_usage_str)
            if parent_block_usage.context_key != library_key:
                raise ValidationError(detail={"parent_block": "Usage ID doesn't match library ID in the URL."})
            result = api.create_library_block_child(parent_block_usage, **serializer.validated_data)
        else:
            # Create a new regular top-level block:
            result = api.create_library_block(library_key, **serializer.validated_data)
        return Response(LibraryXBlockMetadataSerializer(result).data)


@view_auth_classes()
class LibraryBlockView(APIView):
    """
    Views to work with an existing XBlock in a content library.
    """
    @convert_exceptions
    def get(self, request, usage_key_str):
        """
        Get metadata about an existing XBlock in the content library
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        result = api.get_library_block(key)
        return Response(LibraryXBlockMetadataSerializer(result).data)

    @convert_exceptions
    def delete(self, request, usage_key_str):  # pylint: disable=unused-argument
        """
        Delete a usage of a block from the library (and any children it has).

        If this is the only usage of the block's definition within this library,
        both the definition and the usage will be deleted. If this is only one
        of several usages, the definition will be kept. Usages by linked bundles
        are ignored and will not prevent deletion of the definition.

        If the usage points to a definition in a linked bundle, the usage will
        be deleted but the link and the linked bundle will be unaffected.
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        api.delete_library_block(key)
        return Response({})


@view_auth_classes()
class LibraryBlockOlxView(APIView):
    """
    Views to work with an existing XBlock's OLX
    """
    @convert_exceptions
    def get(self, request, usage_key_str):
        """
        Get the block's OLX
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        xml_str = api.get_library_block_olx(key)
        return Response(LibraryXBlockOlxSerializer({"olx": xml_str}).data)

    @convert_exceptions
    def post(self, request, usage_key_str):
        """
        Replace the block's OLX.

        This API is only meant for use by developers or API client applications.
        Very little validation is done.
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        serializer = LibraryXBlockOlxSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_olx_str = serializer.validated_data["olx"]
        try:
            api.set_library_block_olx(key, new_olx_str)
        except ValueError as err:
            raise ValidationError(detail=str(err))
        return Response(LibraryXBlockOlxSerializer({"olx": new_olx_str}).data)


@view_auth_classes()
class LibraryBlockAssetListView(APIView):
    """
    Views to list an existing XBlock's static asset files
    """
    @convert_exceptions
    def get(self, request, usage_key_str):
        """
        List the static asset files belonging to this block.
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        files = api.get_library_block_static_asset_files(key)
        return Response(LibraryXBlockStaticFilesSerializer({"files": files}).data)


@view_auth_classes()
class LibraryBlockAssetView(APIView):
    """
    Views to work with an existing XBlock's static asset files
    """
    parser_classes = (MultiPartParser, )

    @convert_exceptions
    def get(self, request, usage_key_str, file_path):
        """
        Get a static asset file belonging to this block.
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        files = api.get_library_block_static_asset_files(key)
        for f in files:
            if f.path == file_path:
                return Response(LibraryXBlockStaticFileSerializer(f).data)
        raise NotFound

    @convert_exceptions
    def put(self, request, usage_key_str, file_path):
        """
        Replace a static asset file belonging to this block.
        """
        usage_key = LibraryUsageLocatorV2.from_string(usage_key_str)
        file_wrapper = request.data['content']
        if file_wrapper.size > 20 * 1024 * 1024:  # > 20 MiB
            # In the future, we need a way to use file_wrapper.chunks() to read
            # the file in chunks and stream that to Blockstore, but Blockstore
            # currently lacks an API for streaming file uploads.
            raise ValidationError("File too big")
        file_content = file_wrapper.read()
        try:
            result = api.add_library_block_static_asset_file(usage_key, file_path, file_content)
        except ValueError:
            raise ValidationError("Invalid file path")
        return Response(LibraryXBlockStaticFileSerializer(result).data)

    @convert_exceptions
    def delete(self, request, usage_key_str, file_path):  # pylint: disable=unused-argument
        """
        Delete a static asset file belonging to this block.
        """
        usage_key = LibraryUsageLocatorV2.from_string(usage_key_str)
        try:
            api.delete_library_block_static_asset_file(usage_key, file_path)
        except ValueError:
            raise ValidationError("Invalid file path")
        return Response(status=status.HTTP_204_NO_CONTENT)
