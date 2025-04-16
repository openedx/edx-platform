"""
Models for the course to library import app.
"""

import uuid as uuid_tools
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from model_utils.models import TimeStampedModel
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.django.models import (
    LearningContextKeyField,
    UsageKeyField,
)
from openedx_learning.api.authoring_models import LearningPackage, PublishableEntity

from .data import ImportStatus

User = get_user_model()


class Import(TimeStampedModel):
    """
    Represents the action of a user importing a modulestore-based course or legacy
    library into a learning-core based learning package (today, that is always a content library).
    """

    uuid = models.UUIDField(default=uuid_tools.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=100, choices=ImportStatus.choices, default=ImportStatus.PENDING, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    source_key = LearningContextKeyField(help_text=_('The modulestore course'), max_length=255, db_index=True)
    target = models.ForeignKey(LearningPackage, models.SET_NULL, null=True)

    class Meta:
        verbose_name = _('Import from modulestore')
        verbose_name_plural = _('Imports from modulestore')

    def __str__(self):
        return f'{self.source_key} - {self.target}'

    def set_status(self, status: ImportStatus):
        """
        Set import status.
        """
        self.status = status
        self.save()
        if status in [ImportStatus.IMPORTED, ImportStatus.CANCELED]:
            self.clean_related_staged_content()

    def clean_related_staged_content(self) -> None:
        """
        Clean related staged content.
        """
        for staged_content_for_import in self.staged_content_for_import.all():
            staged_content_for_import.staged_content.delete()

    def get_staged_content_by_block_usage_key(self, block_usage_key: str | UsageKey) -> Optional["StagedContent"]:
        """
        Get staged content by block usage key.
        """
        staged_content_for_import = self.staged_content_for_import.filter(
            staged_content__tags__icontains=block_usage_key
        ).first()
        return staged_content_for_import.staged_content if staged_content_for_import else None


class PublishableEntityMapping(TimeStampedModel):
    """
    Represents a mapping between a source usage key and a target publishable entity.
    """

    source_usage_key = UsageKeyField(
        max_length=255,
        help_text=_('Original usage key/ID of the thing that has been imported.'),
    )
    target_package = models.ForeignKey(LearningPackage, on_delete=models.CASCADE)
    target_entity = models.ForeignKey(PublishableEntity, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('source_usage_key', 'target_package')

    def __str__(self):
        return f'{self.source_usage_key} - {self.target_entity}'


class PublishableEntityImport(TimeStampedModel):
    """
    Represents a publishableentity version that has been imported into a learning package (e.g. content library)
    This is a many-to-many relationship between a container version and a course to library import.
    """

    import_event = models.ForeignKey(Import, on_delete=models.CASCADE)
    result = models.ForeignKey(PublishableEntityMapping, on_delete=models.SET_NULL, null=True, blank=True)
    resulting_draft = models.OneToOneField(
        to='oel_publishing.PublishableEntityVersion',
        # a version can be pruned, which would set this to NULL, but not delete the
        # entire import record
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        unique_together = (
            ('import_event', 'result'),
        )

    def __str__(self):
        return f'{self.import_event} - {self.result}'


class StagedContentForImport(TimeStampedModel):
    """
    Represents m2m relationship between an import and staged content created for that import.
    """

    import_event = models.ForeignKey(
        Import,
        on_delete=models.CASCADE,
        related_name='staged_content_for_import',
    )
    staged_content = models.OneToOneField(
        to='content_staging.StagedContent',
        on_delete=models.CASCADE,
        related_name='staged_content_for_import',
    )

    class Meta:
        unique_together = (
            ('import_event', 'staged_content'),
        )

    def __str__(self):
        return f'{self.import_event} - {self.staged_content}'
