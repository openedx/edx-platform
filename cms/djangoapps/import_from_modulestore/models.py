"""
Models for the course to library import app.
"""
from typing import Self

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from user_tasks.models import UserTaskStatus

from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import (
    LearningContextKeyField,
    UsageKeyField,
)
from openedx_learning.api.authoring_models import LearningPackage, PublishableEntity

from .data import CompositionLevel, ImportStatus

User = get_user_model()


class Import(models.Model):
    """
    Represents the action of a user importing a modulestore-based course or legacy
    library into a learning-core based learning package (today, that is always a content library).
    """

    user_task_status = models.OneToOneField(
        UserTaskStatus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_event',
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Note: For now, this will always be a course key. In the future, it may be a legacy library key.
    source_key = LearningContextKeyField(help_text=_('The modulestore course'), max_length=255, db_index=True)
    target_change = models.ForeignKey(to='oel_publishing.DraftChangeLog', on_delete=models.SET_NULL, null=True)
    composition_level = models.CharField(
        max_length=255,
        choices=CompositionLevel.choices(),
        help_text=_('The composition level of the target learning package'),
        default=CompositionLevel.COMPONENT.value,
    )
    override = models.BooleanField(
        default=False,
        help_text=_(
            'If true, the import will override any existing content in the target learning package.'
        ),
    )

    class Meta:
        verbose_name = _('Import from modulestore')
        verbose_name_plural = _('Imports from modulestore')

    def __str__(self):
        return f'{self.source_key} → {self.target_change}'

    def set_status(self: Self, status: ImportStatus):
        """
        Set import status.
        """
        user_task_status: UserTaskStatus = self.user_task_status

        if status in ImportStatus.FAILED_STATUSES.value:
            user_task_status.fail(status.value)
        elif status == ImportStatus.CANCELED:
            user_task_status.cancel()
        else:
            user_task_status.set_state(status.value)

        user_task_status.save()

        if status in [ImportStatus.IMPORTED, ImportStatus.CANCELED]:
            self.clean_related_staged_content()

    def clean_related_staged_content(self) -> None:
        """
        Clean related staged content.
        """
        for staged_content_for_import in self.staged_content_for_import.all():
            staged_content_for_import.staged_content.delete()


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
        return f'{self.source_usage_key} → {self.target_entity}'


class PublishableEntityImport(TimeStampedModel):
    """
    Represents a publishableentity version that has been imported into a learning package (e.g. content library)

    This is a many-to-many relationship between a container version and a course to library import.
    """

    import_event = models.ForeignKey(Import, on_delete=models.CASCADE)
    resulting_mapping = models.ForeignKey(PublishableEntityMapping, on_delete=models.SET_NULL, null=True, blank=True)
    resulting_change = models.OneToOneField(
        to='oel_publishing.DraftChangeLogRecord',
        # a changelog record can be pruned, which would set this to NULL, but not delete the
        # entire import record
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        unique_together = (
            ('import_event', 'resulting_mapping'),
        )

    def __str__(self):
        return f'{self.import_event} → {self.resulting_mapping}'


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
    # Since StagedContent stores all the keys of the saved blocks, this field was added to optimize search.
    source_usage_key = UsageKeyField(
        max_length=255,
        help_text=_(
            'The original Usage key of the highest-level component that was saved in StagedContent.'
        ),
    )

    class Meta:
        unique_together = (
            ('import_event', 'staged_content'),
        )

    def __str__(self):
        return f'{self.import_event} → {self.staged_content}'
