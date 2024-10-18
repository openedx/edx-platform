"""
=======================
Content Libraries Views
=======================

This module contains the REST APIs for Learning Core-based content libraries,
and LTI 1.3 views (though I'm not sure how functional the LTI piece of this is
right now).

Most of the real work is intended to happen in the api.py module. The views are
intended to be thin ones that do:

1. Permissions checking
2. Input/output data conversion via serializers
3. Pagination

Everything else should be delegated to api.py for the actual business logic. If
you see business logic happening in these views, consider refactoring them into
the api module instead.

.. warning::
    **NOTICE: DO NOT USE THE @atomic DECORATOR FOR THESE VIEWS!!!**

    Views in ths module are decorated with:
      @method_decorator(non_atomic_requests, name="dispatch")

    This forces the views to execute without an implicit view-level transaction,
    even if the project is configured to use view-level transactions by default.
    (So no matter what you set the ATOMIC_REQUESTS setting to.)

    We *must* use manual transactions for content libraries related views, or
    we'll run into mysterious race condition bugs. We should NOT use the @atomic
    decorator over any of these views.

    The problem is this: Code outside of this app will want to listen for
    content lifecycle events like ``LIBRARY_BLOCK_CREATED`` and take certain
    actions based on them. We see this pattern used extensively with courses.
    Another common pattern is to use celery to queue up an asynchronous task to
    do that work.

    If there is an implicit database transaction around the entire view
    execution, the celery task may start up just before the view finishes
    executing. When that happens, the celery task doesn't see the new content
    change, because the view transaction hasn't finished committing it to the
    database yet.

    The worst part of this is that dev environments and tests often won't catch
    this because celery is typically configured to run in-process in those
    situations. When it's run in-process, celery is already inside the view's
    transaction so it will "see" the new changes and everything will appear to
    be fine–only to fail intermittently when deployed to production.

    We can and should continue to use atomic() as a context manager when we want
    to make changes to multiple models. But this should happen at the api module
    layer, not in the view. Other apps are permitted to call functions in the
    public api.py module, and we want to make sure those api calls manage their
    own transactions and don't assume that they're being called in an atomic
    block.

    Historical note: These views used to be wrapped with @atomic because we
    wanted to make all views that operated on Blockstore (the predecessor
    to Learning Core) atomic:
        https://github.com/openedx/edx-platform/pull/30456
"""

from functools import wraps
import itertools
import json
import logging

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic, non_atomic_requests
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_safe
from django.views.generic.base import TemplateResponseMixin, View
from pylti1p3.contrib.django import DjangoCacheDataStorage, DjangoDbToolConf, DjangoMessageLaunch, DjangoOIDCLogin
from pylti1p3.exception import LtiException, OIDCException

import edx_api_doc_tools as apidocs
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_learning.api import authoring
from organizations.api import ensure_organization
from organizations.exceptions import InvalidOrganizationException
from organizations.models import Organization
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from openedx.core.djangoapps.content_libraries import api, permissions
from openedx.core.djangoapps.content_libraries.serializers import (
    ContentLibraryBlockImportTaskCreateSerializer,
    ContentLibraryBlockImportTaskSerializer,
    ContentLibraryFilterSerializer,
    ContentLibraryMetadataSerializer,
    ContentLibraryPermissionLevelSerializer,
    ContentLibraryPermissionSerializer,
    ContentLibraryUpdateSerializer,
    ContentLibraryComponentCollectionsUpdateSerializer,
    LibraryXBlockCreationSerializer,
    LibraryXBlockMetadataSerializer,
    LibraryXBlockTypeSerializer,
    LibraryXBlockOlxSerializer,
    LibraryXBlockStaticFileSerializer,
    LibraryXBlockStaticFilesSerializer,
    ContentLibraryAddPermissionByEmailSerializer,
    LibraryPasteClipboardSerializer,
)
import openedx.core.djangoapps.site_configuration.helpers as configuration_helpers
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.djangoapps.safe_sessions.middleware import mark_user_change_as_expected
from openedx.core.djangoapps.xblock import api as xblock_api

from .models import ContentLibrary, LtiGradedResource, LtiProfile


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
        except InvalidKeyError as exc:
            log.exception(str(exc))
            raise NotFound  # lint-amnesty, pylint: disable=raise-missing-from
        except api.ContentLibraryNotFound:
            log.exception("Content library not found")
            raise NotFound  # lint-amnesty, pylint: disable=raise-missing-from
        except api.ContentLibraryBlockNotFound:
            log.exception("XBlock not found in content library")
            raise NotFound  # lint-amnesty, pylint: disable=raise-missing-from
        except api.ContentLibraryCollectionNotFound:
            log.exception("Collection not found in content library")
            raise NotFound  # lint-amnesty, pylint: disable=raise-missing-from
        except api.LibraryCollectionAlreadyExists as exc:
            log.exception(str(exc))
            raise ValidationError(str(exc))  # lint-amnesty, pylint: disable=raise-missing-from
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


class LibraryApiPaginationDocs:
    """
    API docs for query params related to paginating ContentLibraryMetadata objects.
    """
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


@method_decorator(non_atomic_requests, name="dispatch")
@view_auth_classes()
class LibraryRootView(GenericAPIView):
    """
    Views to list, search for, and create content libraries.
    """

    @apidocs.schema(
        parameters=[
            *LibraryApiPaginationDocs.apidoc_params,
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
            apidocs.query_parameter(
                'order',
                str,
                description=(
                    "Name of the content library field to sort the results by. Prefix with a '-' to sort descending."
                ),
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
        order = serializer.validated_data['order']

        queryset = api.get_libraries_for_user(
            request.user,
            org=org,
            library_type=library_type,
            text_search=text_search,
            order=order,
        )
        paginated_qs = self.paginate_queryset(queryset)
        result = api.get_metadata(paginated_qs)

        serializer = ContentLibraryMetadataSerializer(result, many=True)
        # Verify `pagination` param to maintain compatibility with older
        # non pagination-aware clients
        if request.GET.get('pagination', 'false').lower() == 'true':
            return self.get_paginated_response(serializer.data)
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
            with atomic():
                result = api.create_library(org=org, **data)
                # Grant the current user admin permissions on the library:
                api.set_library_user_permissions(result.key, request.user, api.AccessLevel.ADMIN_LEVEL)
        except api.LibraryAlreadyExists:
            raise ValidationError(detail={"slug": "A library with that ID already exists."})  # lint-amnesty, pylint: disable=raise-missing-from

        return Response(ContentLibraryMetadataSerializer(result).data)


@method_decorator(non_atomic_requests, name="dispatch")
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
        serializer = ContentLibraryMetadataSerializer(result, context={'request': self.request})
        return Response(serializer.data)

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

    @convert_exceptions
    def delete(self, request, lib_key_str):  # pylint: disable=unused-argument
        """
        Delete a content library
        """
        key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(key, request.user, permissions.CAN_DELETE_THIS_CONTENT_LIBRARY)
        api.delete_library(key)
        return Response({})


@method_decorator(non_atomic_requests, name="dispatch")
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


@method_decorator(non_atomic_requests, name="dispatch")
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
            raise ValidationError(detail=str(err))  # lint-amnesty, pylint: disable=raise-missing-from
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
            raise ValidationError(detail=str(err))  # lint-amnesty, pylint: disable=raise-missing-from
        return Response({})


@method_decorator(non_atomic_requests, name="dispatch")
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


@method_decorator(non_atomic_requests, name="dispatch")
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


@method_decorator(non_atomic_requests, name="dispatch")
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
        api.publish_changes(key, request.user.id)
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


@method_decorator(non_atomic_requests, name="dispatch")
@view_auth_classes()
class LibraryPasteClipboardView(GenericAPIView):
    """
    Paste content of clipboard into Library.
    """
    @convert_exceptions
    def post(self, request, lib_key_str):
        """
        Import the contents of the user's clipboard and paste them into the Library
        """
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(library_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        serializer = LibraryPasteClipboardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = api.import_staged_content_from_user_clipboard(
                library_key, request.user, **serializer.validated_data
            )
        except api.IncompatibleTypesError as err:
            raise ValidationError(  # lint-amnesty, pylint: disable=raise-missing-from
                detail={'block_type': str(err)},
            )

        return Response(LibraryXBlockMetadataSerializer(result).data)


@method_decorator(non_atomic_requests, name="dispatch")
@view_auth_classes()
class LibraryBlocksView(GenericAPIView):
    """
    Views to work with XBlocks in a specific content library.
    """

    @apidocs.schema(
        parameters=[
            *LibraryApiPaginationDocs.apidoc_params,
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
        components = api.get_library_components(key, text_search=text_search, block_types=block_types)

        paginated_xblock_metadata = [
            api.LibraryXBlockMetadata.from_component(key, component)
            for component in self.paginate_queryset(components)
        ]
        serializer = LibraryXBlockMetadataSerializer(paginated_xblock_metadata, many=True)
        return self.get_paginated_response(serializer.data)

    @convert_exceptions
    def post(self, request, lib_key_str):
        """
        Add a new XBlock to this content library
        """
        library_key = LibraryLocatorV2.from_string(lib_key_str)
        api.require_permission_for_library_key(library_key, request.user, permissions.CAN_EDIT_THIS_CONTENT_LIBRARY)
        serializer = LibraryXBlockCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create a new regular top-level block:
        try:
            result = api.create_library_block(library_key, user_id=request.user.id, **serializer.validated_data)
        except api.IncompatibleTypesError as err:
            raise ValidationError(  # lint-amnesty, pylint: disable=raise-missing-from
                detail={'block_type': str(err)},
            )

        return Response(LibraryXBlockMetadataSerializer(result).data)


@method_decorator(non_atomic_requests, name="dispatch")
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
        result = api.get_library_block(key, include_collections=True)

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


@method_decorator(non_atomic_requests, name="dispatch")
@view_auth_classes()
class LibraryBlockCollectionsView(APIView):
    """
    View to set collections for a component.
    """
    @convert_exceptions
    def patch(self, request, usage_key_str) -> Response:
        """
        Sets Collections for a Component.

        Collection and Components must all be part of the given library/learning package.
        """
        key = LibraryUsageLocatorV2.from_string(usage_key_str)
        content_library = api.require_permission_for_library_key(
            key.lib_key,
            request.user,
            permissions.CAN_EDIT_THIS_CONTENT_LIBRARY
        )
        component = api.get_component_from_usage_key(key)
        serializer = ContentLibraryComponentCollectionsUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        collection_keys = serializer.validated_data['collection_keys']
        api.set_library_component_collections(
            library_key=key.lib_key,
            component=component,
            collection_keys=collection_keys,
            created_by=self.request.user.id,
            content_library=content_library,
        )

        return Response({'count': len(collection_keys)})


@method_decorator(non_atomic_requests, name="dispatch")
@view_auth_classes()
class LibraryBlockLtiUrlView(APIView):
    """
    Views to generate LTI URL for existing XBlocks in a content library.

    Returns 404 in case the block not found by the given key.
    """
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


@method_decorator(non_atomic_requests, name="dispatch")
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
        xml_str = xblock_api.get_block_draft_olx(key)
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
            version_num = api.set_library_block_olx(key, new_olx_str)
        except ValueError as err:
            raise ValidationError(detail=str(err))  # lint-amnesty, pylint: disable=raise-missing-from
        return Response(LibraryXBlockOlxSerializer({"olx": new_olx_str, "version_num": version_num}).data)


@method_decorator(non_atomic_requests, name="dispatch")
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


@method_decorator(non_atomic_requests, name="dispatch")
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
            # TODO: This check was written when V2 Libraries were backed by the Blockstore micro-service.
            #       Now that we're on Learning Core, do we still need it? Here's the original comment:
            #         In the future, we need a way to use file_wrapper.chunks() to read
            #         the file in chunks and stream that to Blockstore, but Blockstore
            #         currently lacks an API for streaming file uploads.
            #       Ref:  https://github.com/openedx/edx-platform/issues/34737
            raise ValidationError("File too big")
        file_content = file_wrapper.read()
        try:
            result = api.add_library_block_static_asset_file(usage_key, file_path, file_content, request.user)
        except ValueError:
            raise ValidationError("Invalid file path")  # lint-amnesty, pylint: disable=raise-missing-from
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
            api.delete_library_block_static_asset_file(usage_key, file_path, request.user)
        except ValueError:
            raise ValidationError("Invalid file path")  # lint-amnesty, pylint: disable=raise-missing-from
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(non_atomic_requests, name="dispatch")
@view_auth_classes()
class LibraryImportTaskViewSet(GenericViewSet):
    """
    Import blocks from Courseware through modulestore.
    """

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

        return self.get_paginated_response(
            self.paginate_queryset(result)
        )

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


@method_decorator(non_atomic_requests, name="dispatch")
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


@method_decorator(non_atomic_requests, name="dispatch")
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


@method_decorator(non_atomic_requests, name="dispatch")
@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(xframe_options_exempt, name='dispatch')
class LtiToolLaunchView(TemplateResponseMixin, LtiToolView):
    """
    LTI platform tool launch view.

    The launch view supports resource link launches and AGS, when enabled by the
    LTI platform.  Other features and resouces are ignored.
    """

    template_name = 'xblock_v2/xblock_iframe.html'

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


@method_decorator(non_atomic_requests, name="dispatch")
class LtiToolJwksView(LtiToolView):
    """
    JSON Web Key Sets view.
    """

    def get(self, request):
        """
        Return the JWKS.
        """
        return JsonResponse(self.lti_tool_config.get_jwks(), safe=False)


@require_safe
def component_version_asset(request, component_version_uuid, asset_path):
    """
    Serves static assets associated with particular Component versions.

    Important notes:
    * This is meant for Studio/authoring use ONLY. It requires read access to
      the content library.
    * It uses the UUID because that's easier to parse than the key field (which
      could be part of an OpaqueKey, but could also be almost anything else).
    * This is not very performant, and we still want to use the X-Accel-Redirect
      method for serving LMS traffic in the longer term (and probably Studio
      eventually).
    """
    try:
        component_version = authoring.get_component_version_by_uuid(
            component_version_uuid
        )
    except ObjectDoesNotExist as exc:
        raise Http404() from exc

    # Permissions check...
    learning_package = component_version.component.learning_package
    library_key = LibraryLocatorV2.from_string(learning_package.key)
    api.require_permission_for_library_key(
        library_key, request.user, permissions.CAN_VIEW_THIS_CONTENT_LIBRARY,
    )

    # We already have logic for getting the correct content and generating the
    # proper headers in Learning Core, but the response generated here is an
    # X-Accel-Redirect and lacks the actual content. We eventually want to use
    # this response in conjunction with a media reverse proxy (Caddy or Nginx),
    # but in the short term we're just going to remove the redirect and stream
    # the content directly.
    redirect_response = authoring.get_redirect_response_for_component_asset(
        component_version_uuid,
        asset_path,
        public=False,
        learner_downloadable_only=False,
    )

    # If there was any error, we return that response because it will have the
    # correct headers set and won't have any X-Accel-Redirect header set.
    if redirect_response.status_code != 200:
        return redirect_response

    # If we got here, we know that the asset exists and it's okay to download.
    cv_content = component_version.componentversioncontent_set.get(key=asset_path)
    content = cv_content.content

    # Delete the re-direct part of the response headers. We'll copy the rest.
    headers = redirect_response.headers
    headers.pop('X-Accel-Redirect')

    # We need to set the content size header manually because this is a
    # streaming response. It's not included in the redirect headers because it's
    # not needed there (the reverse-proxy would have direct access to the file).
    headers['Content-Length'] = content.size

    if request.method == "HEAD":
        return HttpResponse(headers=headers)

    # Otherwise it's going to be a GET response. We don't support response
    # offsets or anything fancy, because we don't expect to run this view at
    # LMS-scale.
    return StreamingHttpResponse(
        content.read_file().chunks(),
        headers=redirect_response.headers,
    )
