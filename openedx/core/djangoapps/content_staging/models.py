"""
Models for content staging (and clipboard)
"""
import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from opaque_keys.edx.django.models import UsageKeyField
from opaque_keys.edx.keys import LearningContextKey

from openedx.core.djangoapps.content.course_overviews.api import get_course_overview_or_none

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
        help_text=_("""
            What type of content is staged. Only OLX content is supported, and
            this field must be the same as the root tag of the OLX.
            e.g. "video" if a video is staged, or "vertical" for a unit.
        """),
    )
    olx = models.TextField(null=False, blank=False)
    # The display name of whatever item is staged here, i.e. the root XBlock.
    display_name = models.CharField(max_length=1024)
    # A _suggested_ URL name to use for this content. Since this suggestion may already be in use, it's fine to generate
    # a new url_name instead.
    suggested_url_name = models.CharField(max_length=1024)

    @property
    def olx_filename(self) -> str:
        """ Get a filename that can be used for the OLX content of this staged content """
        return f"{self.suggested_url_name}.xml"


class UserClipboard(models.Model):
    """
    Each user has a clipboard that can hold one item at a time, where an item
    is some OLX content that can be used in a course, such as an XBlock, a Unit,
    or a Subsection.
    """
    # The user that copied something. Clipboards are user-specific and
    # previously copied items are not kept.
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    content = models.ForeignKey(StagedContent, on_delete=models.CASCADE)
    source_usage_key = UsageKeyField(
        max_length=255,
        help_text=_("Original usage key/ID of the thing that is in the clipboard."),
    )

    @property
    def source_context_key(self) -> LearningContextKey:
        """ Get the context (course/library) that this was copied from """
        return self.source_usage_key.context_key

    def get_source_context_title(self) -> str:
        """ Get the title of the source context, if any """
        if self.source_context_key.is_course:
            course_overview = get_course_overview_or_none(self.source_context_key)
            if course_overview:
                return course_overview.display_name_with_default
        # Just return the ID as the name, if it's empty or is not a course.
        return str(self.source_context_key)

    def clean(self):
        """ Check that this model is being used correctly. """
        # These could probably be replaced with constraints in Django 4.1+
        if self.user.id != self.content.user.id:
            raise ValidationError("User ID mismatch.")
        if self.content.purpose != StagedContent.Purpose.CLIPBOARD:
            raise ValidationError("StagedContent.purpose must be Purpose.CLIPBOARD to use it as clipboard content.")

    def save(self, *args, **kwargs):
        """ Save this model instance """
        # Enforce checks on save:
        self.full_clean()
        return super().save(*args, **kwargs)
