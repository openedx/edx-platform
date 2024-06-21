"""
Public python API for content staging
"""
from __future__ import annotations

from django.http import HttpRequest
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import AssetKey, UsageKey

from .data import StagedContentData, StagedContentFileData, StagedContentStatus, UserClipboardData
from .models import UserClipboard as _UserClipboard, StagedContent as _StagedContent
from .serializers import UserClipboardSerializer as _UserClipboardSerializer


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
    content = clipboard.content
    if only_ready and content.status != StagedContentStatus.READY:
        # The clipboard content is LOADING, ERROR, or EXPIRED
        return None
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
        ),
        source_usage_key=clipboard.source_usage_key,
    )


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
    serializer = _UserClipboardSerializer(clipboard, context={'request': request})
    return serializer.data


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
