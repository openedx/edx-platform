"""
=======================
Content Libraries Views
=======================

This module contains the REST APIs for blockstore-based content libraries, and
LTI 1.3 views.
"""


from functools import wraps
import itertools
import json
import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.db.transaction import atomic
from django.http import Http404
from django.http import HttpResponseBadRequest
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.base import View
from pylti1p3.contrib.django import DjangoCacheDataStorage
from pylti1p3.contrib.django import DjangoDbToolConf
from pylti1p3.contrib.django import DjangoMessageLaunch
from pylti1p3.contrib.django import DjangoOIDCLogin
from pylti1p3.exception import LtiException
from pylti1p3.exception import OIDCException

import edx_api_doc_tools as apidocs
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from organizations.api import ensure_organization
from organizations.exceptions import InvalidOrganizationException
from organizations.models import Organization
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.serializers import (
    ContentLibraryBlockImportTaskCreateSerializer,
    ContentLibraryBlockImportTaskSerializer,
    ContentLibraryFilterSerializer,
    ContentLibraryMetadataSerializer,
    ContentLibraryPermissionLevelSerializer,
    ContentLibraryPermissionSerializer,
    ContentLibraryUpdateSerializer,
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
import openedx.core.djangoapps.site_configuration.helpers as configuration_helpers
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.djangoapps.safe_sessions.middleware import mark_user_change_as_expected
from openedx.core.djangoapps.xblock import api as xblock_api

from .models import ContentLibrary
from .models import LtiGradedResource
from .models import LtiProfile


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
            raise NotFound  # lint-amnesty, pylint: disable=raise-missing-from
        except api.ContentLibraryBlockNotFound:
            log.exception("XBlock not found in content library")
            raise NotFound  # lint-amnesty, pylint: disable=raise-missing-from
        except api.LibraryBlockAlreadyExists as exc:
            log.exception(str(exc))
            raise ValidationError(str(exc))  # lint-amnesty, pylint: disable=raise-missing-from
        except api.InvalidNameError as exc:
            log.exception(str(exc))
            raise ValidationError(str(exc))  # lint-amnesty, pylint: disable=raise-missing-from
        except api.BlockLimitReachedError as exc:
            log.exception(str(exc))
            raise ValidationError(str(exc))  # lint-amnesty, pylint: disable=raise-missing-from
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

    @atomic
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

    @atomic
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
        key_data = data.pop("key")
        # Move "slug" out of the "key.slug" pseudo-field that the serializer added:
        data["slug"] = key_data["slug"]
        # Get the organization short_name out of the "key.org" pseudo-field that the serializer added:
        org_name = key_data["org"]
        try:
            ensure_organization(org_name)
        except InvalidOrganizationException:
            raise ValidationError(  # lint-amnesty, pylint: disable=raise-missing-from
                detail={"org": f"No such organization '{org_name}' found."}
            )
        org = Organization.objects.get(short_name=org_name)
        try:
            result = api.create_library(org=org, **data)
        except api.LibraryAlreadyExists:
            raise ValidationError(detail={"slug": "A library with that ID already exists."})  # lint-amnesty, pylint: disable=raise-missing-from
        # Grant the current user admin permissions on the library:
        api.set_library_user_permissions(result.key, request.user, api.AccessLevel.ADMIN_LEVEL)
        return Response(ContentLibraryMetadataSerializer(result).data)


@view_auth_classes()
class LibraryDetailsView(APIView):
    """
    Views to work with a specific content library
    """
    @atomic
    @convert_exceptions
    def get(self, request, lib_key_str):
        """
        Get a specific content library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
        result = api.get_library(key)
        return Response(ContentLibraryMetadataSerializer(result).data)

    @atomic
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
            raise ValidationError({'type': str(err)})  # lint-amnesty, pylint: disable=raise-missing-from
        result = api.get_library(key)
        return Response(ContentLibraryMetadataSerializer(result).data)

    @atomic
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
    @atomic
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
            raise ValidationError({'email': _('We could not find a user with that email address.')})  # lint-amnesty, pylint: disable=raise-missing-from
        grant = api.get_library_user_permissions(key, user)
        if grant:
            return Response(
                {'email': [_('This user already has access to this library.')]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            api.set_library_user_permissions(key, user, access_level=serializer.validated_data["access_level"])
        except api.LibraryPermissionIntegrityError as err:
            raise ValidationError(detail=str(err))  # lint-amnesty, pylint: disable=raise-missing-from
        grant = api.get_library_user_permissions(key, user)
        return Response(ContentLibraryPermissionSerializer(grant).data)

    @atomic
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
    @atomic
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
            raise ValidationError(detail=str(err))  # lint-amnesty, pylint: disable=raise-missing-from
        grant = api.get_library_user_permissions(key, user)
        return Response(ContentLibraryPermissionSerializer(grant).data)

    @atomic
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

    @atomic
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
            raise ValidationError(detail=str(err))  # lint-amnesty, pylint: disable=raise-missing-from
        return Response({})


@view_auth_classes()
class LibraryTeamGroupView(APIView):
    """
    View to add/remove/edit a group's permissions for a content library.
    """
    @atomic
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

    @atomic
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
    @atomic
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
    @atomic
    @convert_exceptions
    def get(self, request, lib_key_str):
        """
        Get the list of bundles that this library links to, if any
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
        result = api.get_bundle_links(key)
        return Response(LibraryBundleLinkSerializer(result, many=True).data)

    @atomic
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
    @atomic
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

    @atomic
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
    @atomic
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

    @atomic
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
    @atomic
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

    @atomic
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
                raise ValidationError(  # lint-amnesty, pylint: disable=raise-missing-from
                    detail={'block_type': str(err)},
                )
        return Response(LibraryXBlockMetadataSerializer(result).data)


@view_auth_classes()
class LibraryBlockView(APIView):
    """
    Views to work with an existing XBlock in a content library.
    """
    @atomic
    @convert_exceptions
    def get(self, request, usage_key_str):
        """
        Get metadata about an existing XBlock in the content library
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        api.require_permission_for_library_key(key.lib_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
        result = api.get_library_block(key)
        return Response(LibraryXBlockMetadataSerializer(result).data)

    @atomic
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
class LibraryBlockLtiUrlView(APIView):
    """
    Views to generate LTI URL for existing XBlocks in a content library.

    Returns 404 in case the block not found by the given key.
    """
    @atomic
    @convert_exceptions
    def get(self, request, usage_key_str):
        """
        Get the LTI launch URL for the XBlock.
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        api.require_permission_for_library_key(key.lib_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)

        # Get the block to validate its existence
        api.get_library_block(key)
        lti_login_url = f"{reverse('content_libraries:lti-launch')}?id={key}"
        return Response({"lti_url": lti_login_url})


@view_auth_classes()
class LibraryBlockOlxView(APIView):
    """
    Views to work with an existing XBlock's OLX
    """
    @atomic
    @convert_exceptions
    def get(self, request, usage_key_str):
        """
        Get the block's OLX
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        api.require_permission_for_library_key(key.lib_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY)
        xml_str = api.get_library_block_olx(key)
        return Response(LibraryXBlockOlxSerializer({"olx": xml_str}).data)

    @atomic
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
            raise ValidationError(detail=str(err))  # lint-amnesty, pylint: disable=raise-missing-from
        return Response(LibraryXBlockOlxSerializer({"olx": new_olx_str}).data)


@view_auth_classes()
class LibraryBlockAssetListView(APIView):
    """
    Views to list an existing XBlock's static asset files
    """
    @atomic
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

    @atomic
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

    @atomic
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
            raise ValidationError("Invalid file path")  # lint-amnesty, pylint: disable=raise-missing-from
        return Response(LibraryXBlockStaticFileSerializer(result).data)

    @atomic
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
            raise ValidationError("Invalid file path")  # lint-amnesty, pylint: disable=raise-missing-from
        return Response(status=status.HTTP_204_NO_CONTENT)


@view_auth_classes()
class LibraryImportTaskViewSet(ViewSet):
    """
    Import blocks from Courseware through modulestore.
    """

    @atomic
    @convert_exceptions
    def list(self, request, lib_key_str):
        """
        List all import tasks for this library.
        """
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(
            library_key,
            request.user,
            permissions.CAN_VIEW_THIS_CONTENT_LIBRARY
        )
        queryset = api.ContentLibrary.objects.get_by_key(library_key).import_tasks
        result = ContentLibraryBlockImportTaskSerializer(queryset, many=True).data
        paginator = LibraryApiPagination()
        return paginator.get_paginated_response(
            paginator.paginate_queryset(result, request)
        )

    @atomic
    @convert_exceptions
    def create(self, request, lib_key_str):
        """
        Create and queue an import tasks for this library.
        """

        library_key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(
            library_key,
            request.user,
            permissions.CAN_EDIT_THIS_CONTENT_LIBRARY,
        )

        serializer = ContentLibraryBlockImportTaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_key = serializer.validated_data['course_key']

        import_task = api.import_blocks_create_task(library_key, course_key)
        return Response(ContentLibraryBlockImportTaskSerializer(import_task).data)

    @atomic
    @convert_exceptions
    def retrieve(self, request, lib_key_str, pk=None):
        """
        Retrieve a import task for inspection.
        """

        library_key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(
            library_key,
            request.user,
            permissions.CAN_VIEW_THIS_CONTENT_LIBRARY,
        )

        import_task = api.ContentLibraryBlockImportTask.objects.get(pk=pk)
        return Response(ContentLibraryBlockImportTaskSerializer(import_task).data)


# LTI 1.3 Views
# =============


def requires_lti_enabled(view_func):
    """
    Modify the view function to raise 404 if content librarie LTI tool was not
    enabled.
    """
    def wrapped_view(*args, **kwargs):
        lti_enabled = (settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES')
                       and settings.FEATURES.get('ENABLE_CONTENT_LIBRARIES_LTI_TOOL'))
        if not lti_enabled:
            raise Http404()
        return view_func(*args, **kwargs)
    return wrapped_view


@method_decorator(requires_lti_enabled, name='dispatch')
class LtiToolView(View):
    """
    Base LTI View initializing common attributes.
    """

    # pylint: disable=attribute-defined-outside-init
    def setup(self, request, *args, **kwds):
        """
        Initialize attributes shared by all LTI views.
        """
        super().setup(request, *args, **kwds)
        self.lti_tool_config = DjangoDbToolConf()
        self.lti_tool_storage = DjangoCacheDataStorage(cache_name='default')


@method_decorator(csrf_exempt, name='dispatch')
class LtiToolLoginView(LtiToolView):
    """
    Third-party Initiated Login view.

    The LTI platform will start the OpenID Connect flow by redirecting the User
    Agent (UA) to this view. The redirect may be a form POST or a GET.  On
    success the view should redirect the UA to the LTI platform's authentication
    URL.
    """

    LAUNCH_URI_PARAMETER = 'target_link_uri'

    def get(self, request):
        return self.post(request)

    def post(self, request):
        """Initialize 3rd-party login requests to redirect."""
        oidc_login = DjangoOIDCLogin(
            self.request,
            self.lti_tool_config,
            launch_data_storage=self.lti_tool_storage)
        launch_url = (self.request.POST.get(self.LAUNCH_URI_PARAMETER)
                      or self.request.GET.get(self.LAUNCH_URI_PARAMETER))
        try:
            return oidc_login.redirect(launch_url)
        except OIDCException as exc:
            # Relying on downstream error messages, attempt to sanitize it up
            # for customer facing errors.
            log.error('LTI OIDC login failed: %s', exc)
            return HttpResponseBadRequest('Invalid LTI login request.')


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
class LtiToolLaunchView(TemplateResponseMixin, LtiToolView):
    """
    LTI platform tool launch view.

    The launch view supports resource link launches and AGS, when enabled by the
    LTI platform.  Other features and resouces are ignored.
    """

    template_name = 'content_libraries/xblock_iframe.html'

    @property
    def launch_data(self):
        return self.launch_message.get_launch_data()

    def _authenticate_and_login(self, usage_key):
        """
        Authenticate and authorize the user for this LTI message launch.

        We automatically create LTI profile for every valid launch, and
        authenticate the LTI user associated with it.
        """

        # Check library authorization.

        if not ContentLibrary.authorize_lti_launch(
                usage_key.lib_key,
                issuer=self.launch_data['iss'],
                client_id=self.launch_data['aud']
        ):
            return None

        # Check LTI profile.

        LtiProfile.objects.get_or_create_from_claims(
            iss=self.launch_data['iss'],
            aud=self.launch_data['aud'],
            sub=self.launch_data['sub'])
        edx_user = authenticate(
            self.request,
            iss=self.launch_data['iss'],
            aud=self.launch_data['aud'],
            sub=self.launch_data['sub'])

        if edx_user is not None:
            login(self.request, edx_user)
            perms = api.get_library_user_permissions(
                usage_key.lib_key,
                self.request.user)
            if not perms:
                api.set_library_user_permissions(
                    usage_key.lib_key,
                    self.request.user,
                    api.AccessLevel.ADMIN_LEVEL)

        return edx_user

    def _bad_request_response(self):
        """
        A default response for bad requests.
        """
        return HttpResponseBadRequest('Invalid LTI tool launch.')

    def get_context_data(self):
        """
        Setup the template context data.
        """

        handler_urls = {
            str(key): xblock_api.get_handler_url(key, 'handler_name', self.request.user)
            for key
            in itertools.chain([self.block.scope_ids.usage_id],
                               getattr(self.block, 'children', []))
        }

        # We are defaulting to student view due to current use case (resource
        # link launches).  Launches within other views are not currently
        # supported.
        fragment = self.block.render('student_view')
        lms_root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
        return {
            'fragment': fragment,
            'handler_urls_json': json.dumps(handler_urls),
            'lms_root_url': lms_root_url,
        }

    def get_launch_message(self):
        """
        Return the LTI 1.3 launch message object for the current request.
        """
        launch_message = DjangoMessageLaunch(
            self.request,
            self.lti_tool_config,
            launch_data_storage=self.lti_tool_storage)
        # This will force the LTI launch validation steps.
        launch_message.get_launch_data()
        return launch_message

    # pylint: disable=attribute-defined-outside-init
    def post(self, request):
        """
        Process LTI platform launch requests.
        """

        # Parse LTI launch message.

        try:
            self.launch_message = self.get_launch_message()
        except LtiException as exc:
            log.exception('LTI 1.3: Tool launch failed: %s', exc)
            return self._bad_request_response()

        log.info("LTI 1.3: Launch message body: %s",
                 json.dumps(self.launch_data))

        # Parse content key.

        usage_key_str = request.GET.get('id')
        if not usage_key_str:
            return self._bad_request_response()
        usage_key = LibraryUsageLocatorV2.from_string(usage_key_str)
        log.info('LTI 1.3: Launch block: id=%s', usage_key)

        # Authenticate the launch and setup LTI profiles.

        edx_user = self._authenticate_and_login(usage_key)
        if not edx_user:
            return self._bad_request_response()

        # Get the block.

        self.block = xblock_api.load_block(
            usage_key,
            user=self.request.user)

        # Handle Assignment and Grade Service request.

        self.handle_ags()

        # Render context and response.
        context = self.get_context_data()
        response = self.render_to_response(context)
        mark_user_change_as_expected(edx_user.id)
        return response

    def handle_ags(self):
        """
        Handle AGS-enabled launches for block in the request.
        """

        # Validate AGS.

        if not self.launch_message.has_ags():
            return

        endpoint_claim = 'https://purl.imsglobal.org/spec/lti-ags/claim/endpoint'
        endpoint = self.launch_data[endpoint_claim]
        required_scopes = [
            'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem',
            'https://purl.imsglobal.org/spec/lti-ags/scope/score'
        ]

        for scope in required_scopes:
            if scope not in endpoint['scope']:
                log.info('LTI 1.3: AGS: LTI platform does not support a required '
                         'scope: %s', scope)
                return
        lineitem = endpoint.get('lineitem')
        if not lineitem:
            log.info("LTI 1.3: AGS: LTI platform didn't pass lineitem, ignoring "
                     "request: %s", endpoint)
            return

        # Create graded resource in the database for the current launch.

        resource_claim = 'https://purl.imsglobal.org/spec/lti/claim/resource_link'
        resource_link = self.launch_data.get(resource_claim)

        resource = LtiGradedResource.objects.upsert_from_ags_launch(
            self.request.user, self.block, endpoint, resource_link
        )

        log.info("LTI 1.3: AGS: Upserted LTI graded resource from launch: %s",
                 resource)


class LtiToolJwksView(LtiToolView):
    """
    JSON Web Key Sets view.
    """

    def get(self, request):
        """
        Return the JWKS.
        """
        return JsonResponse(self.lti_tool_config.get_jwks(), safe=False)
