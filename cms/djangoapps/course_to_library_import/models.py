"""
Models for the course to library import app.
"""

import uuid as uuid_tools
from typing import Self

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from opaque_keys.edx.django.models import UsageKeyField

from model_utils.models import TimeStampedModel

from .data import CourseToLibraryImportStatus
from .validators import validate_course_ids

User = get_user_model()


class CourseToLibraryImport(TimeStampedModel):
    """
    Represents a course import into a content library.
    """

    uuid = models.UUIDField(default=uuid_tools.uuid4, editable=False, unique=True, db_index=True)
    status = models.CharField(
        max_length=100,
        choices=CourseToLibraryImportStatus.choices,
        default=CourseToLibraryImportStatus.PENDING
    )
    course_ids = models.TextField(
        blank=False,
        help_text=_('Whitespace-separated list of course keys for which to compute grades.'),
        validators=[validate_course_ids]
    )
    library_key = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.course_ids} - {self.library_key}'

    class Meta:
        verbose_name = _('Course to Library Import')
        verbose_name_plural = _('Course to Library Imports')

    @classmethod
    def get_by_id(cls, import_id: int) -> Self | None:
        """
        Get an import task by its ID.
        """
        return cls.objects.filter(id=import_id).first()

    @classmethod
    def get_ready_by_uuid(cls, import_uuid: str) -> Self | None:
        """
        Get an import task by its UUID.
        """
        return cls.objects.filter(uuid=import_uuid, status=CourseToLibraryImportStatus.READY).first()


class ComponentVersionImport(TimeStampedModel):
    """
    Represents a component version that has been imported into a content library.
    This is a many-to-many relationship between a component version and a course to library import.
    """

    component_version = models.OneToOneField(
        to='oel_components.ComponentVersion',
        on_delete=models.CASCADE
    )
    source_usage_key = UsageKeyField(max_length=255)
    library_import = models.ForeignKey(CourseToLibraryImport, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.component_version} - {self.source_usage_key}'

    class Meta:
        verbose_name = _('Component Version Import')
        verbose_name_plural = _('Component Version Imports')


class ContainerVersionImport(TimeStampedModel):
    """
    Represents a container version that has been imported into a content library.
    This is a many-to-many relationship between a container version and a course to library import.
    """

    container_version = models.OneToOneField(
        to='oel_publishing.ContainerVersion',
        on_delete=models.CASCADE
    )
    source_usage_key = UsageKeyField(max_length=255)
    library_import = models.ForeignKey(CourseToLibraryImport, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.container_version} - {self.source_usage_key}'

    class Meta:
        verbose_name = _('Container Version Import')
        verbose_name_plural = _('Container Version Imports')
