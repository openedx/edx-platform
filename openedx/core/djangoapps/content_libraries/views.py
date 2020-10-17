"""
REST API for Blockstore-based content libraries
"""
from functools import wraps
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
import edx_api_doc_tools as apidocs
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from organizations.models import Organization
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.serializers import (
    ContentLibraryMetadataSerializer,
    ContentLibraryUpdateSerializer,
    ContentLibraryPermissionLevelSerializer,
    ContentLibraryPermissionSerializer,
    ContentLibraryFilterSerializer,
    LibraryXBlockCreationSerializer,
    LibraryXBlockMetadataSerializer,
    LibraryXBlockTypeSerializer,
    LibraryBundleLinkSerializer,
    LibraryBundleLinkUpdateSerializer,
    LibraryXBlockOlxSerializer,
    LibraryXBlockStaticFileSerializer,
    LibraryXBlockStaticFilesSerializer,
    ContentLibraryAddPermissionByEmailSerializer,
)
from openedx.core.lib.api.view_utils import view_auth_classes

User = get_user_model()
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
            log.exception(str(exc))
            raise ValidationError(str(exc))
        except api.InvalidNameError as exc:
            log.exception(str(exc))
            raise ValidationError(str(exc))
        except api.BlockLimitReachedError as exc:
            log.exception(str(exc))
            raise ValidationError(str(exc))
    return wrapped_fn


class LibraryApiPagination(PageNumberPagination):
    """
    Paginates over ContentLibraryMetadata objects.
    """
    page_size = 50
    page_size_query_param = 'page_size'

    apidoc_params = [
        apidocs.query_parameter(
            'pagination',
            bool,
            description="Enables paginated schema",
        ),
        apidocs.query_parameter(
            'page',
            int,
            description="Page number of result. Defaults to 1",
        ),
        apidocs.query_parameter(
            'page_size',
            int,
            description="Page size of the result. Defaults to 50",
        ),
    ]


@view_auth_classes()
class LibraryRootView(APIView):
    """
    Views to list, search for, and create content libraries.
    """

    @apidocs.schema(
        parameters=[
            *LibraryApiPagination.apidoc_params,
            apidocs.query_parameter(
                'org',
                str,
                description="The organization short-name used to filter libraries",
            ),
            apidocs.query_parameter(
                'text_search',
                str,
                description="The string used to filter libraries by searching in title, id, org, or description",
            ),
        ],
    )
    def get(self, request):
        """
        Return a list of all content libraries that the user has permission to view.
        """
        serializer = ContentLibraryFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        org = serializer.validated_data['org']
        library_type = serializer.validated_data['type']
        text_search = serializer.validated_data['text_search']

        paginator = LibraryApiPagination()
        queryset = api.get_libraries_for_user(request.user, org=org, library_type=library_type)
        if text_search:
            result = api.get_metadata_from_index(queryset, text_search=text_search)
            result = paginator.paginate_queryset(result, request)
        else:
            # We can paginate queryset early and prevent fetching unneeded metadata
            paginated_qs = paginator.paginate_queryset(queryset, request)
            result = api.get_metadata_from_index(paginated_qs)

        serializer = ContentLibraryMetadataSerializer(result, many=True)
        # Verify `pagination` param to maintain compatibility with older
        # non pagination-aware clients
        if request.GET.get('pagination', 'false').lower() == 'true':
            return paginator.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def post(self, request):
        """
        Create a new content library.
        """
        if not request.user.has_perm(permissions.CAN_CREATE_CONTENT_LIBRARY):
            raise PermissionDenied
        serializer = ContentLibraryMetadataSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        # Converting this over because using the reserved names 'type' and 'license' would shadow the built-in
        # definitions elsewhere.
        data['library_type'] = data.pop('type')
        data['library_license'] = data.pop('license')
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
        api.require_permission_for_library_key(key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
        result = api.get_library(key)
        return Response(ContentLibraryMetadataSerializer(result).data)

    @convert_exceptions
    def patch(self, request, lib_key_str):
        """
        Update a content library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        serializer = ContentLibraryUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        # Prevent ourselves from shadowing global names.
        if 'type' in data:
            data['library_type'] = data.pop('type')
        if 'license' in data:
            data['library_license'] = data.pop('license')
        try:
            api.update_library(key, **data)
        except api.IncompatibleTypesError as err:
            raise ValidationError({'type': str(err)})
        result = api.get_library(key)
        return Response(ContentLibraryMetadataSerializer(result).data)

    @convert_exceptions
    def delete(self, request, lib_key_str):  # pylint: disable=unused-argument
        """
        Delete a content library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_DELETE_THIS_CONTENT_LIBRARY)
        api.delete_library(key)
        return Response({})


@view_auth_classes()
class LibraryTeamView(APIView):
    """
    View to get the list of users/groups who can access and edit the content
    library.

    Note also the 'allow_public_' settings which can be edited by PATCHing the
    library itself (LibraryDetailsView.patch).
    """
    @convert_exceptions
    def post(self, request, lib_key_str):
        """
        Add a user to this content library via email, with permissions specified in the
        request body.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY_TEAM)
        serializer = ContentLibraryAddPermissionByEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=serializer.validated_data.get('email'))
        except User.DoesNotExist:
            raise ValidationError({'email': _('We could not find a user with that email address.')})
        grant = api.get_library_user_permissions(key, user)
        if grant:
            return Response(
                {'email': [_('This user already has access to this library.')]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            api.set_library_user_permissions(key, user, access_level=serializer.validated_data["access_level"])
        except api.LibraryPermissionIntegrityError as err:
            raise ValidationError(detail=str(err))
        grant = api.get_library_user_permissions(key, user)
        return Response(ContentLibraryPermissionSerializer(grant).data)

    @convert_exceptions
    def get(self, request, lib_key_str):
        """
        Get the list of users and groups who have permissions to view and edit
        this library.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY_TEAM)
        team = api.get_library_team(key)
        return Response(ContentLibraryPermissionSerializer(team, many=True).data)


@view_auth_classes()
class LibraryTeamUserView(APIView):
    """
    View to add/remove/edit an individual user's permissions for a content
    library.
    """
    @convert_exceptions
    def put(self, request, lib_key_str, username):
        """
        Add a user to this content library, with permissions specified in the
        request body.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY_TEAM)
        serializer = ContentLibraryPermissionLevelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, username=username)
        try:
            api.set_library_user_permissions(key, user, access_level=serializer.validated_data["access_level"])
        except api.LibraryPermissionIntegrityError as err:
            raise ValidationError(detail=str(err))
        grant = api.get_library_user_permissions(key, user)
        return Response(ContentLibraryPermissionSerializer(grant).data)

    @convert_exceptions
    def get(self, request, lib_key_str, username):
        """
        Gets the current permissions settings for a particular user.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY_TEAM)
        user = get_object_or_404(User, username=username)
        grant = api.get_library_user_permissions(key, user)
        if not grant:
            raise NotFound
        return Response(ContentLibraryPermissionSerializer(grant).data)

    @convert_exceptions
    def delete(self, request, lib_key_str, username):
        """
        Remove the specified user's permission to access or edit this content
        library.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY_TEAM)
        user = get_object_or_404(User, username=username)
        try:
            api.set_library_user_permissions(key, user, access_level=None)
        except api.LibraryPermissionIntegrityError as err:
            raise ValidationError(detail=str(err))
        return Response({})


@view_auth_classes()
class LibraryTeamGroupView(APIView):
    """
    View to add/remove/edit a group's permissions for a content library.
    """
    @convert_exceptions
    def put(self, request, lib_key_str, group_name):
        """
        Add a group to this content library, with permissions specified in the
        request body.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY_TEAM)
        serializer = ContentLibraryPermissionLevelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = get_object_or_404(Group, name=group_name)
        api.set_library_group_permissions(key, group, access_level=serializer.validated_data["access_level"])
        return Response({})

    @convert_exceptions
    def delete(self, request, lib_key_str, username):
        """
        Remove the specified user's permission to access or edit this content
        library.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY_TEAM)
        group = get_object_or_404(Group, username=username)
        api.set_library_group_permissions(key, group, access_level=None)
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
        api.require_permission_for_library_key(key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
        result = api.get_allowed_block_types(key)
        return Response(LibraryXBlockTypeSerializer(result, many=True).data)


@view_auth_classes()
class LibraryLinksView(APIView):
    """
    View to get the list of bundles/libraries linked to this content library.

    Because every content library is a blockstore bundle, it can have "links" to
    other bundles, which may or may not be content libraries. This allows using
    XBlocks (or perhaps even static assets etc.) from another bundle without
    needing to duplicate/copy the data.

    Links always point to a specific published version of the target bundle.
    Links are identified by a slug-like ID, e.g. "link1"
    """
    @convert_exceptions
    def get(self, request, lib_key_str):
        """
        Get the list of bundles that this library links to, if any
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
        result = api.get_bundle_links(key)
        return Response(LibraryBundleLinkSerializer(result, many=True).data)

    @convert_exceptions
    def post(self, request, lib_key_str):
        """
        Create a new link in this library.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        serializer = LibraryBundleLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_key = LibraryLocatorV2.from_string(serializer.validated_data['opaque_key'])
        api.create_bundle_link(
            library_key=key,
            link_id=serializer.validated_data['id'],
            target_opaque_key=target_key,
            version=serializer.validated_data['version'],  # a number, or None for "use latest version"
        )
        return Response({})


@view_auth_classes()
class LibraryLinkDetailView(APIView):
    """
    View to update/delete an existing library link
    """
    @convert_exceptions
    def patch(self, request, lib_key_str, link_id):
        """
        Update the specified link to point to a different version of its
        target bundle.

        Pass e.g. {"version": 40} or pass {"version": None} to update to the
        latest published version.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        serializer = LibraryBundleLinkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api.update_bundle_link(key, link_id, version=serializer.validated_data['version'])
        return Response({})

    @convert_exceptions
    def delete(self, request, lib_key_str, link_id):  # pylint: disable=unused-argument
        """
        Delete a link from this library.
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        api.update_bundle_link(key, link_id, delete=True)
        return Response({})


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
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        api.publish_changes(key)
        return Response({})

    @convert_exceptions
    def delete(self, request, lib_key_str):  # pylint: disable=unused-argument
        """
        Revert the draft changes made to the specified block and its
        descendants. Restore it to the last published version
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        api.revert_changes(key)
        return Response({})


@view_auth_classes()
class LibraryBlocksView(APIView):
    """
    Views to work with XBlocks in a specific content library.
    """
    @apidocs.schema(
        parameters=[
            *LibraryApiPagination.apidoc_params,
            apidocs.query_parameter(
                'text_search',
                str,
                description="The string used to filter libraries by searching in title, id, org, or description",
            ),
            apidocs.query_parameter(
                'block_type',
                str,
                description="The block type to search for. If omitted or blank, searches for all types. "
                            "May be specified multiple times to match multiple types."
            )
        ],
    )
    @convert_exceptions
    def get(self, request, lib_key_str):
        """
        Get the list of all top-level blocks in this content library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        text_search = request.query_params.get('text_search', None)
        block_types = request.query_params.getlist('block_type') or None

        api.require_permission_for_library_key(key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
        result = api.get_library_blocks(key, text_search=text_search, block_types=block_types)

        # Verify `pagination` param to maintain compatibility with older
        # non pagination-aware clients
        if request.GET.get('pagination', 'false').lower() == 'true':
            paginator = LibraryApiPagination()
            result = paginator.paginate_queryset(result, request)
            serializer = LibraryXBlockMetadataSerializer(result, many=True)
            return paginator.get_paginated_response(serializer.data)

        return Response(LibraryXBlockMetadataSerializer(result, many=True).data)

    @convert_exceptions
    def post(self, request, lib_key_str):
        """
        Add a new XBlock to this content library
        """
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(library_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
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
            try:
                result = api.create_library_block(library_key, **serializer.validated_data)
            except api.IncompatibleTypesError as err:
                raise ValidationError(
                    detail={'block_type': str(err)},
                )
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
        api.require_permission_for_library_key(key.lib_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
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
        api.require_permission_for_library_key(key.lib_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
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
        api.require_permission_for_library_key(key.lib_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
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
        api.require_permission_for_library_key(key.lib_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
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
        api.require_permission_for_library_key(key.lib_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
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
        api.require_permission_for_library_key(key.lib_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
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
        api.require_permission_for_library_key(
            usage_key.lib_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY,
        )
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
    def delete(self, request, usage_key_str, file_path):
        """
        Delete a static asset file belonging to this block.
        """
        usage_key = LibraryUsageLocatorV2.from_string(usage_key_str)
        api.require_permission_for_library_key(
            usage_key.lib_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY,
        )
        try:
            api.delete_library_block_static_asset_file(usage_key, file_path)
        except ValueError:
            raise ValidationError("Invalid file path")
        return Response(status=status.HTTP_204_NO_CONTENT)
