"""
Public python API for content staging
"""
from __future__ import annotations
from datetime import datetime
from typing import NamedTuple

from django.http import HttpRequest
from opaque_keys.edx.keys import UsageKey

from .models import UserClipboard as _UserClipboard, StagedContent as _StagedContent
from .serializers import UserClipboardSerializer as _UserClipboardSerializer


StagedContentStatus = _StagedContent.Status
CLIPBOARD_PURPOSE = _UserClipboard.PURPOSE


class StagedContentData(NamedTuple):
    """ Read-only data model for StagedContent """
    id: int
    user_id: int
    created: datetime
    purpose: str
    status: StagedContentStatus
    block_type: str
    display_name: str


class UserClipboardData(NamedTuple):
    """ Read-only data model for StagedContent """
    content: StagedContentData
    source_usage_key: UsageKey


def get_user_clipboard_status(user_id: int) -> UserClipboardData:
    """ Get the detailed status of the user's clipboard. """
    try:
        clipboard = _UserClipboard.objects.get(user_id=user_id)
    except _UserClipboard.DoesNotExist:
        # This user does not have any content on their clipboard.
        return None
    content = clipboard.content
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


def get_user_clipboard_status_json(user_id: int, request: HttpRequest = None):
    """
    Get the detailed status of the user's clipboard.
    This is _exactly_ the same format as returned from the
        /api/content-staging/v1/clipboard/
    API endpoint. This does not return the OLX.

    (request is optional; including it will make the "olx_url" absolute instead
    of relative.)
    """
    try:
        clipboard = _UserClipboard.objects.get(user_id=user_id)
    except _UserClipboard.DoesNotExist:
        # This user does not have any content on their clipboard.
        return {"content": None, "source_usage_key": "", "source_context_title": ""}
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
