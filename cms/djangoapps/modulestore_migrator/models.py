"""
Models for the modulestore migration tool.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _
from user_tasks.models import UserTaskStatus

from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import (
    LearningContextKeyField,
    UsageKeyField,
)
from openedx_learning.api.authoring_models import (
    LearningPackage, PublishableEntity, Collection, DraftChangeLog, DraftChangeLogRecord
)

from openedx.core.djangoapps.content_staging.models import StagedContent
from .data import CompositionLevel

User = get_user_model()


class ModulestoreSource(models.Model):
    """
    A legacy learning context (course or library) which can be a source of a migration.
    """
    key = LearningContextKeyField(
        max_length=255,
        unique=True,
        help_text=_('Key of the content source (a course or a legacy library)'),
    )
    forwarded = models.OneToOneField(
        'modulestore_migrator.ModulestoreMigration',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_('If set, the system will forward references of this source over to the target of this migration'),
        related_name="forwards",
    )

    def __str__(self):
        return f"{self.__class__.__name__}('{self.key}')"

    __repr__ = __str__


class ModulestoreMigration(models.Model):
    """
    Tracks the action of a user importing a Modulestore-based course or legacy library into a
    learning-core based learning package

    Notes:
    * As of Ulmo, a learning package is always associated with a v2 content library, but we
      will not bake that assumption into this model)
    * Each Migration is tied to a single UserTaskStatus, which connects it to a user and
      contains the progress of the import.
    * A single ModulestoreSource may very well have multiple ModulestoreMigrations; however,
      at most one of them with be the "authoritative" migration, as indicated by `forwarded`.
    """

    ## MIGRATION SPECIFICATION
    source = models.ForeignKey(
        ModulestoreSource,
        on_delete=models.CASCADE,
        related_name="migrations",
    )
    composition_level = models.CharField(
        max_length=255,
        choices=CompositionLevel.supported_choices(),
        default=CompositionLevel.Component.value,
        help_text=_('Maximum hierachy level at which content should be aggregated in target library'),
    )
    replace_existing = models.BooleanField(
        default=False,
        help_text=_(
            "If a piece of content already exists in the content library, should the import process replace it?"
        ),
    )
    target = models.ForeignKey(
        LearningPackage,
        on_delete=models.CASCADE,
        help_text=_('Content will be imported into this library'),
    )
    target_collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_('Optional - Collection (within the target library) into which imported content will be grouped'),
    )

    ## MIGRATION ARTIFACTS
    task_status = models.OneToOneField(
        UserTaskStatus,
        on_delete=models.RESTRICT,
        help_text=_("Tracks the status of the task which is executing this migration"),
    )
    change_log = models.ForeignKey(
        DraftChangeLog,
        on_delete=models.SET_NULL,
        null=True,
        help_text=_("Changelog entry in the target learning package which records this migration"),
    )
    staged_content = models.OneToOneField(
        StagedContent,
        null=True,
        on_delete=models.SET_NULL,  # Staged content is liable to be deleted in order to save space
        help_text=_(
            "Modulestore content is processed and staged before importing it to a learning packge. "
            "We temporarily save the staged content to allow for troubleshooting of failed migrations."
        )
    )

    def __str__(self):
        return (
            f"{self.__class__.__name__} #{self.pk}: "
            f"{self.source.key} → {self.target_collection or self.target}"
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"id={self.id}, source='{self.source}',"
            f"target='{self.target_collection or self.target}')"
        )


class ModulestoreBlockSource(TimeStampedModel):
    """
    A legacy block usage (in a course or library) which can be a source of a block migration.
    """
    overall_source = models.ForeignKey(
        ModulestoreSource,
        on_delete=models.CASCADE,
        related_name="blocks",
    )
    key = UsageKeyField(
        max_length=255,
        help_text=_('Original usage key of the XBlock that has been imported.'),
    )
    forwarded = models.OneToOneField(
        'modulestore_migrator.ModulestoreBlockMigration',
        null=True,
        on_delete=models.SET_NULL,
        help_text=_(
            'If set, the system will forward references of this block source over to the target of this block migration'
        ),
        related_name="forwards",
    )
    unique_together = [("overall_source", "key")]

    def __str__(self):
        return f"{self.__class__.__name__}('{self.key}')"

    __repr__ = __str__


class ModulestoreBlockMigration(TimeStampedModel):
    """
    The migration of a single legacy block into a learning package.

    Is always tied to a greater overall ModulestoreMigration.

    Note:
    * A single ModulestoreBlockSource may very well have multiple ModulestoreBlockMigrations; however,
      at most one of them with be the "authoritative" migration, as indicated by `forwarded`.
      This will coincide with the `overall_migration` being pointed to by `forwarded` as well.
    """
    overall_migration = models.ForeignKey(
        ModulestoreMigration,
        on_delete=models.CASCADE,
        related_name="block_migrations",
    )
    source = models.ForeignKey(
        ModulestoreBlockSource,
        on_delete=models.CASCADE,
    )
    target = models.ForeignKey(
        PublishableEntity,
        on_delete=models.CASCADE,
    )
    change_log_record = models.OneToOneField(
        DraftChangeLogRecord,
        # a changelog record can be pruned, which would set this to NULL, but not delete the
        # entire import record
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        unique_together = [
            ('overall_migration', 'source'),
            ('overall_migration', 'target'),
        ]

    def __str__(self):
        return (
            f"{self.__class__.__name__} #{self.pk}: "
            f"{self.source.key} → {self.target}"
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"id={self.id}, source='{self.source}',"
            f"target='{self.target}')"
        )
