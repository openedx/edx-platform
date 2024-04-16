"""
REST API views for content staging
"""
from __future__ import annotations
import hashlib
import logging

from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
import edx_api_doc_tools as apidocs
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import CourseLocator
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from common.djangoapps.student.auth import has_studio_read_access

from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.lib.xblock_serializer.api import serialize_xblock_to_olx, StaticFile
from xmodule import block_metadata_utils
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .data import CLIPBOARD_PURPOSE, StagedContentStatus
from .models import StagedContent, StagedContentFile, UserClipboard
from .serializers import UserClipboardSerializer, PostToClipboardSerializer
from .tasks import delete_expired_clipboards

log = logging.getLogger(__name__)


@view_auth_classes(is_authenticated=True)
class StagedContentOLXEndpoint(APIView):
    """
    API Endpoint to get the OLX of any given StagedContent.
    """

    def get(self, request, id):  # pylint: disable=redefined-builtin
        """
        Get the OLX of the given StagedContent object.
        """
        staged_content = get_object_or_404(StagedContent, pk=id)
        if staged_content.user.id != request.user.id:
            raise PermissionDenied("Users can only access their own staged content")
        if staged_content.status != StagedContentStatus.READY:
            # If the status is LOADING, the OLX may not be generated/valid yet.
            # If the status is ERROR or EXPIRED, this row is no longer usable.
            raise NotFound("The requested content is not available.")
        return HttpResponse(staged_content.olx, headers={
            "Content-Type": f"application/vnd.openedx.xblock.v1.{staged_content.block_type}+xml",
            "Content-Disposition": f'attachment; filename="{staged_content.olx_filename}"',
        })


@method_decorator(transaction.non_atomic_requests, name='dispatch')
@view_auth_classes(is_authenticated=True)
class ClipboardEndpoint(APIView):
    """
    API Endpoint that can be used to get the status of the current user's
    clipboard or to POST some content to the clipboard.
    """

    @apidocs.schema(
        responses={
            200: UserClipboardSerializer,
        }
    )
    def get(self, request):
        """
        Get the detailed status of the user's clipboard. This does not return the OLX.
        """
        try:
            clipboard = UserClipboard.objects.get(user=request.user.id)
        except UserClipboard.DoesNotExist:
            # This user does not have any content on their clipboard.
            return Response({
                "content": None,
                "source_usage_key": "",
                "source_context_title": "",
                "source_edit_url": "",
            })
        serializer = UserClipboardSerializer(clipboard, context={"request": request})
        return Response(serializer.data)

    @apidocs.schema(
        body=PostToClipboardSerializer,
        responses={
            200: UserClipboardSerializer,
            403: "You do not have permission to read the specified usage key.",
            404: "The requested usage key does not exist.",
        },
    )
    def post(self, request):
        """
        Put some piece of content into the user's clipboard.
        """
        # Check if the content exists and the user has permission to read it.
        # Parse the usage key:
        try:
            usage_key = UsageKey.from_string(request.data["usage_key"])
        except (ValueError, InvalidKeyError):
            raise ValidationError('Invalid usage key')  # lint-amnesty, pylint: disable=raise-missing-from
        if usage_key.block_type in ('course', 'chapter', 'sequential'):
            raise ValidationError('Requested XBlock tree is too large')
        course_key = usage_key.context_key
        if not isinstance(course_key, CourseLocator):
            # In the future, we'll support libraries too but for now we don't.
            raise ValidationError('Invalid usage key: not a modulestore course')
        # Make sure the user has permission on that course
        if not has_studio_read_access(request.user, course_key):
            raise PermissionDenied("You must be a member of the course team in Studio to export OLX using this API.")

        # Get the OLX of the content
        try:
            block = modulestore().get_item(usage_key)
        except ItemNotFoundError as exc:
            raise NotFound("The requested usage key does not exist.") from exc
        block_data = serialize_xblock_to_olx(block)

        expired_ids = []
        with transaction.atomic():
            # Mark all of the user's existing StagedContent rows as EXPIRED
            to_expire = StagedContent.objects.filter(
                user=request.user,
                purpose=CLIPBOARD_PURPOSE,
            ).exclude(
                status=StagedContentStatus.EXPIRED,
            )
            for sc in to_expire:
                expired_ids.append(sc.id)
                sc.status = StagedContentStatus.EXPIRED
                sc.save()
            # Insert a new StagedContent row for this
            staged_content = StagedContent.objects.create(
                user=request.user,
                purpose=CLIPBOARD_PURPOSE,
                status=StagedContentStatus.READY,
                block_type=usage_key.block_type,
                olx=block_data.olx_str,
                display_name=block_metadata_utils.display_name_with_default(block),
                suggested_url_name=usage_key.block_id,
                tags=block_data.tags,
            )
            (clipboard, _created) = UserClipboard.objects.update_or_create(user=request.user, defaults={
                "content": staged_content,
                "source_usage_key": usage_key,
            })
            # Return the current clipboard exactly as if GET was called:
            serializer = UserClipboardSerializer(clipboard, context={"request": request})
            # Log an event so we can analyze how this feature is used:
            log.info(f"Copied {usage_key.block_type} component \"{usage_key}\" to their clipboard.")

        # Try to copy the static files. If this fails, we still consider the overall copy attempt to have succeeded,
        # because intra-course pasting will still work fine, and in any case users can manually resolve the file issue.
        try:
            self._save_static_assets_to_clipboard(block_data.static_files, usage_key, staged_content)
        except Exception:  # pylint: disable=broad-except
            # Regardless of what happened, with get_asset_key_from_path or contentstore or run_filter, we don't want the
            # whole "copy to clipboard" operation to fail, which would be a bad user experience. For copying and pasting
            # within a single course, static assets don't even matter. So any such errors become warnings here.
            log.exception(f"Unable to copy static files to clipboard for component {usage_key}")

        # Enqueue a (potentially slow) task to delete the old staged content
        try:
            delete_expired_clipboards.delay(expired_ids)
        except Exception:  # pylint: disable=broad-except
            log.exception(f"Unable to enqueue cleanup task for StagedContents: {','.join(str(x) for x in expired_ids)}")
        # Return the response:
        return Response(serializer.data)

    @staticmethod
    def _save_static_assets_to_clipboard(
        static_files: list[StaticFile], usage_key: UsageKey, staged_content: StagedContent
    ):
        """
        Helper method for "post to clipboard" API endpoint. This deals with copying static files into the clipboard.
        """
        for f in static_files:
            source_key = (
                StaticContent.get_asset_key_from_path(usage_key.context_key, f.url)
                if (f.url and f.url.startswith('/')) else None
            )
            # Compute the MD5 hash and get the content:
            content: bytes | None = f.data
            md5_hash = ""  # Unknown
            if content:
                md5_hash = hashlib.md5(content).hexdigest()
                # This asset came from the XBlock's filesystem, e.g. a video block's transcript file
                source_key = usage_key
            # Check if the asset file exists. It can be absent if an XBlock contains an invalid link.
            elif source_key and (sc := contentstore().find(source_key, throw_on_not_found=False)):
                md5_hash = sc.content_digest
                content = sc.data
            else:
                continue  # Skip this file - we don't need a reference to a non-existent file.

            # Because we store clipboard files on S3, uploading really large files will be too slow. And it's wasted if
            # the copy-paste is just happening within a single course. So for files > 10MB, users must copy the files
            # manually. In the future we can consider removing this or making it configurable or filterable.
            limit = 10 * 1024 * 1024
            if content and len(content) > limit:
                content = None

            try:
                StagedContentFile.objects.create(
                    for_content=staged_content,
                    filename=f.name,
                    # In some cases (e.g. really large files), we don't store the data here but we still keep track of
                    # the metadata. You can still use the metadata to determine if the file is already present or not,
                    # and then either inform the user or find another way to import the file (e.g. if the file still
                    # exists in the "Files & Uploads" contentstore of the source course, based on source_key_str).
                    data_file=ContentFile(content=content, name=f.name) if content else None,
                    source_key_str=str(source_key) if source_key else "",
                    md5_hash=md5_hash,
                )
            except Exception:  # pylint: disable=broad-except
                log.exception(f"Unable to copy static file {f.name} to clipboard for component {usage_key}")
