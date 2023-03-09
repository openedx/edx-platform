"""
Models for content staging (and clipboard)
"""
from __future__ import annotations  # in lieu of typing.Self
import logging
# from typing import Self # Needs Python 3.11

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from opaque_keys.edx.django.models import LearningContextKeyField

log = logging.getLogger(__name__)

User = get_user_model()

class StagedContent(models.Model):
    """
    Each StagedContent instance represents a "piece" of content (e.g. a single
    XBlock, or a single Unit, or a single Subsection of a course) that is not
    currently part of any course or library, but which is available to be copied
    into a course or library.

    Use as a clipboard: for any given user, the most recent row with
    purpose=CLIPBOARD is the "current" clipboard content. But it can only be
    pasted if its status is READY.
    """

    class Purpose(models.TextChoices):
        """ The purpose of this staged content. """
        CLIPBOARD = "clipboard", _("Clipboard")

    class Status(models.TextChoices):
        """ The status of this staged content. """
        # LOADING: We are actively (asynchronously) writing the OLX and related data into the staging area.
        # It is not ready to be read.
        LOADING = "loading", _("Loading")
        # READY: The content is staged and ready to be read.
        READY = "ready", _("Ready")
        # The content has expired and this row can be deleted, along with any associated data.
        EXPIRED = "expired", _("Expired")
        # ERROR: The content could not be staged.
        ERROR = "error", _("Error")

    id = models.AutoField(primary_key=True)
    # The user that created and owns this staged content. Only this user can read it.
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    created = models.DateTimeField(null=False, auto_now_add=True)
    # What this StagedContent is for
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    status = models.CharField(max_length=20, choices=Status.choices)

    block_type = models.CharField(
        max_length=100,
        help_text=("""
            What type of content is staged. Only OLX content is supported, and
            this field must be the same as the root tag of the OLX.
            e.g. "video" if a video is staged, or "vertical" for a unit.
        """),
    )
    olx = models.TextField(null=False, blank=False)
    # The display name of whatever item is staged here, i.e. the root XBlock.
    display_name = models.CharField(max_length=1024)
    # What course or library this content comes from, if it exists in the CMS already. If it doesn't, leave this blank.
    source_context = LearningContextKeyField(max_length=255)

    @classmethod
    def get_clipboard_content(cls, user_id: int) -> StagedContent|None:
        return cls.objects.filter(
            user_id=user_id,
            purpose=cls.Purpose.CLIPBOARD,
        ).order_by("-created").first()


# class UserClipboard(models.Model):
#     """
#     Each user has a clipboard that can hold one item at a time, where an item
#     is some OLX content that can be used in a course, such as an XBlock, a Unit,
#     or a Subsection.
#     """
#     # The user that copied something. Clipboards are user-specific and
#     # previously copied items are not kept.
#     user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
#     content = models.ForeignKey(StagedContent, on_delete=models.CASCADE)




