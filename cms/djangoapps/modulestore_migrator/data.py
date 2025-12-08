"""
Value objects
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from django.utils.translation import gettext_lazy as _
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import (
    CourseLocator,
    LibraryContainerLocator,
    LibraryLocator,
    LibraryLocatorV2,
    LibraryUsageLocatorV2,
)
from openedx_learning.api.authoring import get_draft_version
from openedx_learning.api.authoring_models import PublishableEntityVersion

from openedx.core.djangoapps.content_libraries.api import ContainerType
from openedx.core.djangoapps.content_libraries.api import (
    library_component_usage_key, library_container_locator
)

from . import models


class CompositionLevel(Enum):
    """
    Enumeration of composition levels for legacy content.

    Defined in increasing order of complexity so that `is_higher_than` works correctly.
    """
    # Components are individual XBlocks, e.g. Problem
    Component = 'component'

    # Container types currently supported by Content Libraries
    Unit = ContainerType.Unit.value
    Subsection = ContainerType.Subsection.value
    Section = ContainerType.Section.value

    @property
    def is_container(self) -> bool:
        return self is not self.Component

    def is_higher_than(self, other: 'CompositionLevel') -> bool:
        """
        Is this composition level 'above' (more complex than) the other?
        """
        levels: list[CompositionLevel] = list(self.__class__)
        return levels.index(self) > levels.index(other)

    @classmethod
    def supported_choices(cls) -> list[tuple[str, str]]:
        """
        Returns all supported composition levels as a list of tuples,
        for use in a Django Models ChoiceField.
        """
        return [
            (composition_level.value, composition_level.name)
            for composition_level in cls
        ]


class RepeatHandlingStrategy(Enum):
    """
    Enumeration of repeat handling strategies for imported content.
    """
    Skip = 'skip'
    Fork = 'fork'
    Update = 'update'

    @classmethod
    def supported_choices(cls) -> list[tuple[str, str]]:
        """
        Returns all supported repeat handling strategies as a list of tuples,
        for use in a Django Models ChoiceField.
        """
        return [
            (strategy.value, strategy.name)
            for strategy in cls
        ]

    @classmethod
    def default(cls) -> RepeatHandlingStrategy:
        """
        Returns the default repeat handling strategy.
        """
        return cls.Skip


SourceContextKey: t.TypeAlias = CourseLocator | LibraryLocator


@dataclass(frozen=True)
class ModulestoreMigration:
    """
    Metadata on a migration 11of a course or legacy library to a v2 library in learning core.
    """
    pk: int
    source_key: SourceContextKey
    target_key: LibraryLocatorV2
    target_title: str
    target_collection_slug: str | None
    target_collection_title: str | None
    is_successful: bool
    failure_info: str | None
    is_authoritative: bool
    task_uuid: UUID  # the UserTask which executed this migration

    @classmethod
    def from_model(cls, m: models.ModulestoreMigration) -> t.Self:
        is_successsful = m.task_status.state == models.UserTaskStatus.SUCCEEDED
        failure_info = None
        if m.task_status.state == models.UserTaskStatus.FAILED:
            if artifact := m.task_status.arifacts.first():
                failure_info = artifact.text
        return cls(
            pk=m.id,
            source_key=m.source.key,
            target_key=LibraryLocatorV2.from_string(m.target.key),
            target_title=m.target.title,
            target_collection_slug=(m.target_collection.key if m.target_collection else None),
            target_collection_title=(m.target_collection.title if m.target_collection else None),
            is_successful=is_successsful,
            is_authoritative=(m.id == m.source.forwarded_id),
            failure_info=failure_info,
            task_uuid=m.task_status.uuid,
        )

    def load_block_mappings(self) -> dict[UsageKey, ModulestoreBlockMigration]:
        """
        Get details about the migrations of each individual block within a course/lib migration.
        """
        return {
            block_migration.source.key: ModulestoreBlockMigration.from_model(
                block_migration, target_library_key=self.target_key
            )
            for block_migration in models.ModulestoreBlockMigration.objects.filter(
                overall_migration_id=self.pk
            ).select_related(
                'target__component__component_type',
                'target__container',
                'target__learning_package'
            )
        }


@dataclass(frozen=True, eq=True)
class ModulestoreBlockMigration:
    """
    Base class for a modulestore block that's been migrated to Learning Core.
    """
    source_key: UsageKey
    target_entity_pk: int | None  # None iff failed
    target_key: LibraryUsageLocatorV2 | LibraryContainerLocator | None  # None iff failed
    target_title: str | None  # None iff failed
    target_version_num: int | None  # None iff failed OR unknown
    unsupported_reason: str | None  # None iff successful

    @property
    def is_successful(self) -> bool:
        return NotImplemented

    @staticmethod
    def from_model(
        m: models.ModulestoreBlockMigration,
        *,
        target_library_key: LibraryLocatorV2 | None = None,
    ) -> ModulestoreBlockMigration:
        """
        Build an instance of this class from a database row

        Optionally, takes a precomputed target_library_key, to save some time.
        """
        if not m.target:
            return ModulestoreFailedBlockMigration(
                source_key=m.source.key,
                target_entity_pk=None,
                target_key=None,
                target_title=None,
                target_version_num=None,
                unsupported_reason=m.unsupported_reason or "",
            )
        if not target_library_key:
            target_library_key = LibraryLocatorV2.from_string(m.target.key)
        # We expect the block migration to have a DraftChangeLogRecord associated with it, which
        # tells us the entity's version number and the title at the point immediately after the
        # migration occured. However, the data model does not guarantee that the record exists.
        # So, if the record is missing, we:
        # * use the latest draft's title, which is good enough, because the title is just there to help users.
        # * use None as the version_num, because we don't want downstream code to make decisions about
        #   syncing, etc based on incorrect version info.
        target_version: PublishableEntityVersion | None = (
            m.change_log_record.new_version if m.change_log_record else None
        )
        if target_version:
            target_title = target_version.title
            target_version_num = target_version.version_num
        else:
            latest_draft = get_draft_version(m.target)
            target_title = latest_draft.title if latest_draft else ""
            target_version_num = None
        if hasattr(m.target, "component"):
            return ModulestoreComponentMigration(
                source_key=m.source.key,
                target_entity_pk=m.target.id,
                target_title=target_title,
                target_version_num=target_version_num,
                unsupported_reason=None,
                target_key=library_component_usage_key(target_library_key, m.target.component),
            )
        elif hasattr(m.target, "container"):
            return ModulestoreContainerMigration(
                source_key=m.source.key,
                target_entity_pk=m.target.id,
                target_title=target_title,
                target_version_num=target_version_num,
                unsupported_reason=None,
                target_key=library_container_locator(target_library_key, m.target.container),
            )
        else:
            raise NotImplementedError(f"Entity is neither a container nor component: {m.target}")


@dataclass(frozen=True)
class ModulestoreSuccessfulBlockMigration(ModulestoreBlockMigration):
    """
    Info on a modulestore block which has been successfully migrated into an LC entity
    """
    target_entity_pk: int
    target_key: LibraryUsageLocatorV2 | LibraryContainerLocator
    target_title: str
    target_version_num: int | None
    unsupported_reason: None

    @property
    def is_successful(self):
        return True


@dataclass(frozen=True)
class ModulestoreComponentMigration(ModulestoreSuccessfulBlockMigration):
    """
    Info on a modulestore block which has been migrated into a LC component
    """
    target_key: LibraryUsageLocatorV2


@dataclass(frozen=True)
class ModulestoreContainerMigration(ModulestoreSuccessfulBlockMigration):
    """
    Info on a modulestore structural block which has been migrated into a LC container
    """
    target_key: LibraryContainerLocator


@dataclass(frozen=True)
class ModulestoreFailedBlockMigration(ModulestoreBlockMigration):
    """
    Info on a modulestore block which failed to be migrated into LC
    """
    target_key: None
    target_entity_pk: None
    target_title: None
    target_version_num: None
    unsupported_reason: str

    @property
    def is_successful(self):
        return False
