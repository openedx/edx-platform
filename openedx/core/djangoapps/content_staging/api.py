"""
Public python API for content staging
"""
from __future__ import annotations

from django.http import HttpRequest

from .data import StagedContentData, StagedContentStatus, UserClipboardData
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
        ),
        source_usage_key=clipboard.source_usage_key,
    )


def get_user_clipboard_json(user_id: int, request: HttpRequest = None):
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
