"""
Value objects
"""
from __future__ import annotations

from enum import Enum

from opaque_keys.edx.locator import (
    CourseLocator, LibraryLocator,
    LibraryLocatorV2, LibraryUsageLocatorV2,
    LibraryContainerLocator,
)
from openedx_learning.api.authoring import get_collection
from openedx_learning.api.authoring_models import Container

from openedx.core.djangoapps.content_libraries.api import (
    get_library, library_component_usage_key, library_container_locator
)
from openedx.core.djangoapps.content_libraries.api import ContainerType


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
    Metadata on a migration of a course or legacy library to a v2 library in learning core.
    """
    source_key: SourceContextKey
    target_key: LibraryLocatorV2
    target_title: str
    target_collection_slug: str | None
    target_collection_title: str | None
    is_authoritative: bool
    task_uuid: UUID  # the UserTask which executed this migration

    @classmethod
    def from_model(cls, m: models.ModulestoreMigration) -> t.Self:
        return cls(
            source_key=m.source_key,
            target_key=LibraryLocatorV2.from_string(m.target.key),
            target_title=m.target.title,
            target_collection_slug=m.target_collection.key,
            target_collection_title=m.target_collection.title,
            is_authoritative=(m.id == m.source.forwarded_id),
            task_uuid=m.task_uuid,
        )

    def load_block_mappings(self) -> dict[UsageKey, ModulestoreBlockMigration]:
        """
        Get details about the migrations of each individual block within a course/lib migration.
        """
        return {
            block_migration.source_key: ModulestoreBlockMigration.from_model(block_migration, self.target_key)
            for block_migration in self.block_migrations.select_related(
                'target__component__component_type',
                'target__container'
                'target__learning_package'
            )
        }


@dataclass(frozen=True)
class ModulestoreBlockMigration:
    """
    Base class for a modulestore block that's been migrated to Learning Core.
    """
    source_key: UsageKey
    target_key: LibraryUsageLocatorV2 | LibraryContainerLocator | None  # None iff failed
    target_title: str | None  # None iff failed
    target_version_num: int | None  # None iff failed OR unknown
    unsupported_reason: str | None  # None iff successful

    @property
    def is_successful(self) -> bool:
        return NotImplemented

    @classmethod
    def from_model(
        cls,
        m: models.ModulestoreBlockMigration,
        *,
        target_library_key: LibraryLocatorV2 | None = None,
    ) -> t.Self:
        """
        Build an instance of this class from a database row

        Optionally, takes a precomputed target_library_key, to save some time.
        """
        if not target_library_key:
            target_library_key = LibraryLocatorV2.from_string(m.target.key)
        if not m.target:
            return ModulestoreFailedBlockMigration(
                source_key=m.source.key,
                target_key=None,
                target_title=None,
                target_version_num=None,
                unsupported_reason=m.unsupported_reason,
            )
        if hasattr(m.target, "component"):
            return ModulestoreComponentMigration(
                source_key=m.source.key,
                target_key=library_component_usage_key(target_library_key, m.target.component),
                target_title=m.target.title,
                target_version_num=m.change_log_record.version_num if m.change_log_record else None,
                unsupported_reason=None,
            )
        elif hasattr(m.target, "container"):
            return ModulestoreContainerMigration(
                source_key=m.source.key,
                target_key=library_container_locator(target_library_key, m.target.container),
                target_title=m.target.title,
                target_version_num=m.change_log_record.version_num if m.change_log_record else None,
                unsupported_reason=None,
            )
        else:
            raise NotImplementedError(f"Entity is neither a container nor component: {m.target}")


@dataclass(frozen=True)
class ModulestoreSuccessfulBlockMigration(ModulestoreBlockMigration):
    """
    Info on a modulestore block which has been successfully migrated into an LC entity
    """
    target_key: LibraryUsageLocatorV2 | LibraryContainerLocator
    target_entity_pk: int
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
    target_title: None
    target_version_num: None
    unsupported_reason: str

    @property
    def is_successful(self):
        return False