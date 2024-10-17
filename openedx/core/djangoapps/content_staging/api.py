"""
Public python API for content staging
"""
from __future__ import annotations

import hashlib
import logging

from django.core.files.base import ContentFile
from django.db import transaction
from django.http import HttpRequest
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import AssetKey, UsageKey
from xblock.core import XBlock

from openedx.core.lib.xblock_serializer.api import serialize_xblock_to_olx, StaticFile
from openedx.core.djangoapps.content.course_overviews.api import get_course_overview_or_none
from xmodule import block_metadata_utils
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore

from .data import (
    CLIPBOARD_PURPOSE,
    StagedContentData, StagedContentFileData, StagedContentStatus, UserClipboardData
)
from .models import (
    UserClipboard as _UserClipboard,
    StagedContent as _StagedContent,
    StagedContentFile as _StagedContentFile,
)
from .serializers import UserClipboardSerializer as _UserClipboardSerializer
from .tasks import delete_expired_clipboards

log = logging.getLogger(__name__)


def save_xblock_to_user_clipboard(block: XBlock, user_id: int, version_num: int | None = None) -> UserClipboardData:
    """
    Copy an XBlock's OLX to the user's clipboard.
    """
    block_data = serialize_xblock_to_olx(block)
    usage_key = block.usage_key

    expired_ids = []
    with transaction.atomic():
        # Mark all of the user's existing StagedContent rows as EXPIRED
        to_expire = _StagedContent.objects.filter(
            user_id=user_id,
            purpose=CLIPBOARD_PURPOSE,
        ).exclude(
            status=StagedContentStatus.EXPIRED,
        )
        for sc in to_expire:
            expired_ids.append(sc.id)
            sc.status = StagedContentStatus.EXPIRED
            sc.save()
        # Insert a new StagedContent row for this
        staged_content = _StagedContent.objects.create(
            user_id=user_id,
            purpose=CLIPBOARD_PURPOSE,
            status=StagedContentStatus.READY,
            block_type=usage_key.block_type,
            olx=block_data.olx_str,
            display_name=block_metadata_utils.display_name_with_default(block),
            suggested_url_name=usage_key.block_id,
            tags=block_data.tags,
            version_num=(version_num or 0),
        )
        (clipboard, _created) = _UserClipboard.objects.update_or_create(user_id=user_id, defaults={
            "content": staged_content,
            "source_usage_key": usage_key,
        })

    # Log an event so we can analyze how this feature is used:
    log.info(f"Copied {usage_key.block_type} component \"{usage_key}\" to their clipboard.")

    # Try to copy the static files. If this fails, we still consider the overall copy attempt to have succeeded,
    # because intra-course pasting will still work fine, and in any case users can manually resolve the file issue.
    try:
        _save_static_assets_to_user_clipboard(block_data.static_files, usage_key, staged_content)
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

    return _user_clipboard_model_to_data(clipboard)


def _save_static_assets_to_user_clipboard(
    static_files: list[StaticFile], usage_key: UsageKey, staged_content: _StagedContent
):
    """
    Helper method for save_xblock_to_user_clipboard endpoint. This deals with copying static files into the clipboard.
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
            _StagedContentFile.objects.create(
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


def get_user_clipboard(user_id: int, only_ready: bool = True) -> UserClipboardData | None:
    """
    Get the details of the user's clipboard.

    By default, will only return a value if the clipboard is READY to use for
    pasting etc. Pass only_ready=False to get the clipboard data regardless.

    To get the actual OLX content, use get_staged_content_olx(content.id)
    """
    try:
        clipboard = _UserClipboard.objects.get(user_id=user_id)
    except _UserClipboard.DoesNotExist:
        # This user does not have any content on their clipboard.
        return None
    if only_ready and clipboard.content.status != StagedContentStatus.READY:
        # The clipboard content is LOADING, ERROR, or EXPIRED
        return None
    return _user_clipboard_model_to_data(clipboard)


def get_user_clipboard_json(user_id: int, request: HttpRequest | None = None):
    """
    Get the detailed status of the user's clipboard, in exactly the same format
    as returned from the
        /api/content-staging/v1/clipboard/
    REST API endpoint. This version of the API is meant for "preloading" that
    REST API endpoint so it can be embedded in a larger response sent to the
    user's browser. If you just want to get the clipboard data from python, use
    get_user_clipboard() instead, since it's fully typed.

    (request is optional; including it will make the "olx_url" absolute instead
    of relative.)
    """
    try:
        clipboard = _UserClipboard.objects.get(user_id=user_id)
    except _UserClipboard.DoesNotExist:
        # This user does not have any content on their clipboard.
        return {"content": None, "source_usage_key": "", "source_context_title": "", "source_edit_url": ""}
    serializer = _UserClipboardSerializer(
        _user_clipboard_model_to_data(clipboard),
        context={'request': request},
    )
    return serializer.data


def _user_clipboard_model_to_data(clipboard: _UserClipboard) -> UserClipboardData:
    """
    Convert a UserClipboard model instance to an immutable data object.
    """
    content = clipboard.content
    source_context_key = clipboard.source_usage_key.context_key
    if source_context_key.is_course and (course_overview := get_course_overview_or_none(source_context_key)):
        source_context_title = course_overview.display_name_with_default
    else:
        source_context_title = str(source_context_key)  # Fall back to stringified context key as a title
    return UserClipboardData(
        content=StagedContentData(
            id=content.id,
            user_id=content.user_id,
            created=content.created,
            purpose=content.purpose,
            status=content.status,
            block_type=content.block_type,
            display_name=content.display_name,
            tags=content.tags,
            version_num=content.version_num,
        ),
        source_usage_key=clipboard.source_usage_key,
        source_context_title=clipboard.get_source_context_title(),
    )


def get_staged_content_olx(staged_content_id: int) -> str | None:
    """
    Get the OLX (as a string) for the given StagedContent.

    Does not check permissions!
    """
    try:
        sc = _StagedContent.objects.get(pk=staged_content_id)
        return sc.olx
    except _StagedContent.DoesNotExist:
        return None


def get_staged_content_static_files(staged_content_id: int) -> list[StagedContentFileData]:
    """
    Get the filenames and metadata for any static files used by the given staged content.

    Does not check permissions!
    """
    sc = _StagedContent.objects.get(pk=staged_content_id)

    def str_to_key(source_key_str: str):
        if not source_key_str:
            return None
        try:
            return AssetKey.from_string(source_key_str)
        except InvalidKeyError:
            return UsageKey.from_string(source_key_str)

    return [
        StagedContentFileData(
            filename=f.filename,
            # For performance, we don't load data unless it's needed, so there's
            # a separate API call for that.
            data=None,
            source_key=str_to_key(f.source_key_str),
            md5_hash=f.md5_hash,
        )
        for f in sc.files.all()
    ]


def get_staged_content_static_file_data(staged_content_id: int, filename: str) -> bytes | None:
    """
    Get the data for the static asset associated with the given staged content.

    Does not check permissions!
    """
    sc = _StagedContent.objects.get(pk=staged_content_id)
    file_data_obj = sc.files.filter(filename=filename).first()
    if file_data_obj:
        return file_data_obj.data_file.open().read()
    return None
