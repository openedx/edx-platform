"""
Tasks for the modulestore_migrator
"""
from __future__ import annotations

import mimetypes
import os
import typing as t
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from itertools import groupby

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify
from django.db import transaction
from edx_django_utils.monitoring import set_code_owner_attribute_from_module
from lxml import etree
from lxml.etree import _ElementTree as XmlTree
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import (
    CourseLocator,
    LibraryContainerLocator,
    LibraryLocator,
    LibraryLocatorV2,
    LibraryUsageLocatorV2
)
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import (
    Collection,
    Component,
    ComponentType,
    LearningPackage,
    PublishableEntity,
    PublishableEntityVersion
)
from user_tasks.tasks import UserTask, UserTaskStatus
from xblock.core import XBlock
from django.utils.translation import gettext_lazy as _

from common.djangoapps.split_modulestore_django.models import SplitModulestoreCourseIndex
from common.djangoapps.util.date_utils import strftime_localized, DEFAULT_DATE_TIME_FORMAT
from openedx.core.djangoapps.content_libraries import api as libraries_api
from openedx.core.djangoapps.content_libraries.api import ContainerType, get_library
from openedx.core.djangoapps.content_staging import api as staging_api
from xmodule.modulestore import exceptions as modulestore_exceptions
from xmodule.modulestore.django import modulestore

from .constants import CONTENT_STAGING_PURPOSE_TEMPLATE
from .data import CompositionLevel, RepeatHandlingStrategy
from .models import ModulestoreBlockMigration, ModulestoreBlockSource, ModulestoreMigration, ModulestoreSource

log = get_task_logger(__name__)


class MigrationStep(Enum):
    """
    Strings representation the state of an in-progress modulestore-to-learning-core import.

    We use these values to set UserTaskStatus.state.
    The other possible UserTaskStatus.state values are the built-in ones:
    UserTaskStatus.{PENDING,FAILED,CANCELED,SUCCEEDED}.
    """
    VALIDATING_INPUT = 'Validating migration parameters'
    CANCELLING_OLD = 'Cancelling any redundant migration tasks'
    LOADING = 'Loading legacy content from ModulesStore'
    STAGING = 'Staging legacy content for import'
    PARSING = 'Parsing staged OLX'
    IMPORTING_ASSETS = 'Importing staged files and resources'
    IMPORTING_STRUCTURE = 'Importing staged content structure'
    UNSTAGING = 'Cleaning staged content'
    MAPPING_OLD_TO_NEW = 'Saving map of legacy content to migrated content'
    FORWARDING = 'Forwarding legacy content to migrated content'
    POPULATING_COLLECTION = 'Assigning imported items to the specified collection'
    BULK_MIGRATION_PREFIX = 'Migrating legacy content'


class _MigrationTask(UserTask):
    """
    Base class for migrate_to_modulestore
    """

    @staticmethod
    def calculate_total_steps(arguments_dict):
        """
        Get number of in-progress steps in importing process, as shown in the UI.
        """
        # We subtract the BULK_MIGRATION_PREFIX
        return len(list(MigrationStep)) - 1


class _BulkMigrationTask(UserTask):
    """
    Base class for bulk_migrate_from_modulestore
    """

    @staticmethod
    def calculate_total_steps(arguments_dict):
        """
        Get number of in-progress steps in importing process, as shown in the UI.

        There are steps that are general for all sources, but there are steps that are repeated in each source.
        All of this is taken into account to make the sum
        """
        sources_count = len(arguments_dict.get('sources_pks', 1))

        # STAGING, PARSING, IMPORTING_ASSETS, IMPORTING_STRUCTURE, MAPPING_OLD_TO_NEW, UNSTAGING
        steps_repeated_count = 6

        return (
            # All migration steps and subtract the BULK_MIGRATION_PREFIX
            len(list(MigrationStep)) - 1
            # We don't want to count these steps again, they will be counted in the operation below.
            - steps_repeated_count
            # Each source repeats all the `steps_repeated_count`
            + steps_repeated_count * sources_count
        )


@dataclass(frozen=True)
class _MigrationContext:
    """
    Context for the migration process.
    """
    existing_source_to_target_keys: dict[  # Note: It's intended to be mutable to reflect changes during migration.
        UsageKey, list[PublishableEntity]
    ]
    target_package_id: int
    target_library_key: LibraryLocatorV2
    source_context_key: CourseKey  # Note: This includes legacy LibraryLocators, which are sneakily CourseKeys.
    content_by_filename: dict[str, int]
    composition_level: CompositionLevel
    repeat_handling_strategy: RepeatHandlingStrategy
    preserve_url_slugs: bool
    created_by: int
    created_at: datetime

    def is_already_migrated(self, source_key: UsageKey) -> bool:
        return source_key in self.existing_source_to_target_keys

    def get_existing_target(self, source_key: UsageKey) -> PublishableEntity:
        """
        Get the target entity for a given source key.

        If the source key is already migrated, return the FIRST target entity.
        If the source key is not found, raise a KeyError.
        """
        if source_key not in self.existing_source_to_target_keys:
            raise KeyError(f"Source key {source_key} not found in existing source to target keys")

        # NOTE: This is a list of PublishableEntities, but we always return the first one.
        return self.existing_source_to_target_keys[source_key][0]

    def add_migration(self, source_key: UsageKey, target: PublishableEntity) -> None:
        """Update the context with a new migration (keeps it current)"""
        if source_key not in self.existing_source_to_target_keys:
            self.existing_source_to_target_keys[source_key] = [target]
        else:
            self.existing_source_to_target_keys[source_key].append(target)

    def get_existing_target_entity_keys(self, base_key: str) -> set[str]:
        return set(
            publishable_entity.key
            for publishable_entity_list in self.existing_source_to_target_keys.values()
            for publishable_entity in publishable_entity_list
            if publishable_entity.key.startswith(base_key)
        )

    @property
    def should_skip_strategy(self) -> bool:
        """
        Determines whether the repeat handling strategy should skip the entity.
        """
        return self.repeat_handling_strategy is RepeatHandlingStrategy.Skip

    @property
    def should_update_strategy(self) -> bool:
        """
        Determines whether the repeat handling strategy should update the entity.
        """
        return self.repeat_handling_strategy is RepeatHandlingStrategy.Update

    @property
    def should_fork_strategy(self) -> bool:
        """
        Determines whether the repeat handling strategy should fork the entity.
        """
        return self.repeat_handling_strategy is RepeatHandlingStrategy.Fork


@dataclass()
class _MigrationSourceData:
    """
    Data related to a ModulestoreSource
    """
    source: ModulestoreSource
    source_root_usage_key: UsageKey
    source_version: str | None
    migration: ModulestoreMigration


def _validate_input(
    status: UserTaskStatus,
    source_pk: int,
    repeat_handling_strategy: str,
    preserve_url_slugs: bool,
    composition_level: str,
    target_package: LearningPackage,
    target_collection: Collection | None,
) -> _MigrationSourceData | None:
    """
    Validates and build the source data related to `source_pk`
    """
    try:
        source = ModulestoreSource.objects.get(pk=source_pk)
    except (ObjectDoesNotExist) as exc:
        status.fail(str(exc))
        return None

    # The Model is used for Course and Legacy Library
    course_index = SplitModulestoreCourseIndex.objects.filter(course_id=source.key).first()
    if isinstance(source.key, CourseLocator):
        source_root_usage_key = source.key.make_usage_key('course', 'course')
        source_version = course_index.published_version if course_index else None
    elif isinstance(source.key, LibraryLocator):
        source_root_usage_key = source.key.make_usage_key('library', 'library')
        source_version = course_index.library_version if course_index else None
    else:
        status.fail(
            f"Not a valid source context key: {source.key}. "
            "Source key must reference a course or a legacy library."
        )
        return None

    migration = ModulestoreMigration.objects.create(
        source=source,
        source_version=source_version,
        composition_level=composition_level,
        repeat_handling_strategy=repeat_handling_strategy,
        preserve_url_slugs=preserve_url_slugs,
        target=target_package,
        target_collection=target_collection,
        task_status=status,
    )

    return _MigrationSourceData(
        source=source,
        source_root_usage_key=source_root_usage_key,
        source_version=source_version,
        migration=migration,
    )


def _cancel_old_tasks(
    source_list: list[ModulestoreSource],
    status: UserTaskStatus,
    target_package: LearningPackage,
    migration_ids_to_exclude: list[int],
) -> None:
    """
    Cancel all migration tasks related to the user and the source list
    """
    # In order to prevent a user from accidentally starting a bunch of identical import tasks...
    migrations_to_cancel = ModulestoreMigration.objects.filter(
        # get all Migration tasks by this user with the same sources and target
        task_status__user=status.user,
        source__in=source_list,
        target=target_package,
    ).select_related('task_status').exclude(
        # (excluding that aren't running)
        task_status__state__in=(UserTaskStatus.CANCELED, UserTaskStatus.FAILED, UserTaskStatus.SUCCEEDED)
    ).exclude(
        # (excluding these migrations themselves)
        id__in=migration_ids_to_exclude
    )
    # ... and cancel their tasks and clean away their staged content.
    for migration_to_cancel in migrations_to_cancel:
        if migration_to_cancel.task_status:
            migration_to_cancel.task_status.cancel()
        if migration_to_cancel.staged_content:
            migration_to_cancel.staged_content.delete()


def _load_xblock(
    status: UserTaskStatus,
    usage_key: UsageKey,
) -> XBlock | None:
    """
    Loads the Xblock for the given usage_key
    """
    try:
        xblock = modulestore().get_item(usage_key)
    except modulestore_exceptions.ItemNotFoundError as exc:
        status.fail(f"Failed to load source item '{usage_key}' from ModuleStore: {exc}")
        return None
    if not xblock:
        status.fail(f"Could not find source item '{usage_key}' in ModuleStore")
        return None
    return xblock


def _import_assets(migration: ModulestoreMigration) -> dict[str, int]:
    """
    Import the assets of the staged content to the migration target
    """
    if migration.staged_content is None:
        return {}

    content_by_filename: dict[str, int] = {}
    now = datetime.now(tz=timezone.utc)
    for staged_content_file_data in staging_api.get_staged_content_static_files(migration.staged_content.id):
        old_path = staged_content_file_data.filename
        file_data = staging_api.get_staged_content_static_file_data(migration.staged_content.id, old_path)
        if not file_data:
            log.error(
                f"Staged content {migration.staged_content.id} included referenced file {old_path}, "
                "but no file data was found."
            )
            continue
        filename = os.path.basename(old_path)
        media_type_str = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        media_type = authoring_api.get_or_create_media_type(media_type_str)
        content_by_filename[filename] = authoring_api.get_or_create_file_content(
            migration.target_id,
            media_type.id,
            data=file_data,
            created=now,
        ).id
    return content_by_filename


def _import_structure(
    migration: ModulestoreMigration,
    source_data: _MigrationSourceData,
    target_library: libraries_api.ContentLibraryMetadata,
    content_by_filename: dict[str, int],
    root_node: XmlTree,
    status: UserTaskStatus,
) -> tuple[t.Any, _MigratedNode]:
    """
    Import the staged content structure into the target Learning Core library.

    Args:
        migration (ModulestoreMigration):
            The migration record representing the ongoing modulestore-to-learning-core migration.
        source_data (_MigrationSourceData):
            Data extracted from the legacy modulestore, including the source root usage key.
            Use `_validate_input()` to generate this data.
        target_library (libraries_api.ContentLibraryMetadata):
            The target library where the new Learning Core content will be created.
        content_by_filename (dict[str, int]):
            A mapping between OLX file names and their associated file IDs in the staging area.
            Use `_import_assets` to generate this content.
        root_node (XmlTree):
            The parsed XML tree representing the root of the staged OLX content.
        status (UserTaskStatus):
            The user task used to record progress and state updates throughout the import.

    Returns:
        tuple[Any, _MigratedNode]:
            A tuple containing:
                - The first element (`change_log`): the bulk draft change log generated by
                  `authoring_api.bulk_draft_changes_for`, containing all the imported changes.
                - The second element (`root_migrated_node`): a `_MigratedNode` object that
                  represents the mapping between the legacy root node and its newly created
                  Learning Core equivalent.
    """
    # "key" is locally unique across all PublishableEntities within
    # a given LearningPackage.
    # We use this mapping to ensure that we don't create duplicate
    # PublishableEntities during the migration process for a given LearningPackage.
    existing_source_to_target_keys: dict[UsageKey, list[PublishableEntity]] = {}
    modulestore_blocks = (
        ModulestoreBlockMigration.objects.filter(overall_migration__target=migration.target.id).order_by("source__key")
    )
    existing_source_to_target_keys = {
        source_key: list(block.target for block in group) for source_key, group in groupby(
            modulestore_blocks, key=lambda x: x.source.key)
    }

    migration_context = _MigrationContext(
        existing_source_to_target_keys=existing_source_to_target_keys,
        target_package_id=migration.target.pk,
        target_library_key=target_library.key,
        source_context_key=source_data.source_root_usage_key.course_key,
        content_by_filename=content_by_filename,
        composition_level=CompositionLevel(migration.composition_level),
        repeat_handling_strategy=RepeatHandlingStrategy(migration.repeat_handling_strategy),
        preserve_url_slugs=migration.preserve_url_slugs,
        created_by=status.user_id,
        created_at=datetime.now(timezone.utc),
    )

    with authoring_api.bulk_draft_changes_for(migration.target.id) as change_log:
        root_migrated_node = _migrate_node(
            context=migration_context,
            source_node=root_node,
        )
    change_log.save()
    return change_log, root_migrated_node


def _forwarding_content(source_data: _MigrationSourceData) -> None:
    """
    Forwarding legacy content to migrated content
    """
    block_migrations = ModulestoreBlockMigration.objects.filter(overall_migration=source_data.migration)
    block_sources_to_block_migrations = {
        block_migration.source: block_migration for block_migration in block_migrations
    }
    for block_source, block_migration in block_sources_to_block_migrations.items():
        block_source.forwarded = block_migration
        block_source.save()

    source_data.source.forwarded = source_data.migration
    source_data.source.save()


def _populate_collection(user_id: int, migration: ModulestoreMigration) -> None:
    """
    Assigning imported items to the specified collection in the migration
    """
    if migration.target_collection is None:
        return

    block_target_pks: list[int] = list(
        ModulestoreBlockMigration.objects.filter(
            overall_migration=migration
        ).values_list('target_id', flat=True)
    )
    if block_target_pks:
        authoring_api.add_to_collection(
            learning_package_id=migration.target.pk,
            key=migration.target_collection.key,
            entities_qset=PublishableEntity.objects.filter(id__in=block_target_pks),
            created_by=user_id,
        )
    else:
        log.warning("No target entities found to add to collection")


def _create_collection(library_key: LibraryLocatorV2, title: str) -> Collection:
    """
    Creates a collection in the given library

    If there's a collection with the same key, try again, adding the attempt number at the end.
    The same is true for the title.
    """
    key = slugify(title)
    collection = None
    attempt = 0
    created_at = strftime_localized(datetime.now(timezone.utc), DEFAULT_DATE_TIME_FORMAT)
    description = f"{_('This collection contains content migrated from a legacy library on')}: {created_at}"
    while not collection:
        modified_key = key if attempt == 0 else key + '-' + str(attempt)
        try:
            # Add transaction here to avoid TransactionManagementError on retry
            with transaction.atomic():
                collection = libraries_api.create_library_collection(
                    library_key=library_key,
                    collection_key=modified_key,
                    title=f"{title}{f'_{attempt}' if attempt > 0 else ''}",
                    description=description,
                )
        except libraries_api.LibraryCollectionAlreadyExists as e:
            attempt += 1
    return collection


@shared_task(base=_MigrationTask, bind=True)
# Note: The decorator @set_code_owner_attribute cannot be used here because the UserTaskMixin
#   does stack inspection and can't handle additional decorators.
def migrate_from_modulestore(
    self: _MigrationTask,
    *,
    user_id: int,
    source_pk: int,
    target_library_key: str,
    target_collection_pk: int | None,
    repeat_handling_strategy: str,
    preserve_url_slugs: bool,
    composition_level: str,
    forward_source_to_target: bool,
) -> None:
    """
    Import a single course or legacy library from modulestore into a V2 legacy library.

    This task performs the end-to-end migration for one legacy source (course or library),
    including staging, parsing OLX, importing assets and structure, and assigning the
    migrated content to the specified target library and collection.

    A new `UserTaskStatus` entry is created for each invocation of this task, meaning
    that each migration runs independently with its own progress tracking and final
    success or failure state.

    If the migration encounters an unrecoverable error at any step (for example, invalid
    OLX, missing assets, or database constraints), the task is marked as **failed** and
    the partial results are rolled back as necessary. The migration state can be queried
    through the REST API endpoint `/api/modulestore_migrator/v1/migrations/<uuid>/`.

    Args:
        self (_MigrationTask):
            The Celery task instance that wraps the user task logic.
        user_id (int):
            The ID of the user initiating the migration.
        source_pk (int):
            Primary key of the modulestore source to migrate.
        target_library_key (str):
            Key of the target V2 library that will receive the imported content.
        target_collection_pk (int | None):
            Optional ID of a target collection to which imported content will be assigned.
        repeat_handling_strategy (str):
            Strategy for handling repeated imports (e.g., "skip", "update").
        preserve_url_slugs (bool):
            Whether to preserve original XBlock URL slugs during import.
        composition_level (str):
            The structural level to migrate (e.g., component, unit, or section).
        forward_source_to_target (bool):
            Whether to forward legacy content references to the migrated content after import.

    See Also:
        - `bulk_migrate_from_modulestore`: Multi-source batch migration equivalent.
        - API docs: `/api/cms/v1/migrations/` for REST behavior and responses.
    """

    # pylint: disable=too-many-statements
    # This is a large function, but breaking it up futher would probably not
    # make it any easier to understand.

    set_code_owner_attribute_from_module(__name__)
    status: UserTaskStatus = self.status

    # Validating input
    status.set_state(MigrationStep.VALIDATING_INPUT.value)
    try:
        target_library = get_library(LibraryLocatorV2.from_string(target_library_key))
        if target_library.learning_package_id is None:
            raise ValueError("Target library has no associated learning package.")

        target_package = LearningPackage.objects.get(pk=target_library.learning_package_id)
        target_collection = Collection.objects.get(pk=target_collection_pk) if target_collection_pk else None
    except (ObjectDoesNotExist, InvalidKeyError) as exc:
        status.fail(str(exc))
        return

    source_data = _validate_input(
        status,
        source_pk,
        repeat_handling_strategy,
        preserve_url_slugs,
        composition_level,
        target_package,
        target_collection,
    )
    if source_data is None:
        # Fail
        return

    migration = source_data.migration
    status.increment_completed_steps()

    # Cancelling old tasks
    status.set_state(MigrationStep.CANCELLING_OLD.value)
    _cancel_old_tasks([source_data.source], status, target_package, [migration.id])
    status.increment_completed_steps()

    # Loading `legacy_root`
    status.set_state(MigrationStep.LOADING)
    legacy_root = _load_xblock(status, source_data.source_root_usage_key)
    if legacy_root is None:
        # Fail
        return
    status.increment_completed_steps()

    # Staging legacy block
    status.set_state(MigrationStep.STAGING.value)
    staged_content = staging_api.stage_xblock_temporarily(
        block=legacy_root,
        user_id=status.user.pk,
        purpose=CONTENT_STAGING_PURPOSE_TEMPLATE.format(source_key=source_data.source.key),
    )
    migration.staged_content = staged_content
    status.increment_completed_steps()

    # Parsing OLX
    status.set_state(MigrationStep.PARSING.value)
    parser = etree.XMLParser(strip_cdata=False)
    try:
        root_node = etree.fromstring(staged_content.olx, parser=parser)
    except etree.ParseError as exc:
        status.fail(f"Failed to parse source OLX (from staged content with id = {staged_content.id}): {exc}")
    status.increment_completed_steps()

    # Importing assets of the legacy block
    status.set_state(MigrationStep.IMPORTING_ASSETS.value)
    content_by_filename = _import_assets(migration)
    status.increment_completed_steps()

    # Importing structure of the legacy block
    status.set_state(MigrationStep.IMPORTING_STRUCTURE.value)
    change_log, root_migrated_node = _import_structure(
        migration,
        source_data,
        target_library,
        content_by_filename,
        root_node,
        status,
    )
    migration.change_log = change_log
    status.increment_completed_steps()

    status.set_state(MigrationStep.UNSTAGING.value)
    staged_content.delete()
    status.increment_completed_steps()

    _create_migration_artifacts_incrementally(
        root_migrated_node=root_migrated_node,
        source=source_data.source,
        migration=migration,
        status=status,
    )
    status.increment_completed_steps()

    # Forwarding legacy content to migrated content
    status.set_state(MigrationStep.FORWARDING.value)
    if forward_source_to_target:
        _forwarding_content(source_data)
    status.increment_completed_steps()

    # Populating the collection
    status.set_state(MigrationStep.POPULATING_COLLECTION.value)
    if target_collection:
        _populate_collection(user_id, migration)
    status.increment_completed_steps()


@shared_task(base=_BulkMigrationTask, bind=True)
# Note: The decorator @set_code_owner_attribute cannot be used here because the UserTaskMixin
#   does stack inspection and can't handle additional decorators.
def bulk_migrate_from_modulestore(
    self: _BulkMigrationTask,
    *,
    user_id: int,
    sources_pks: list[int],
    target_library_key: str,
    target_collection_pks: list[int | None],
    create_collections: bool = False,
    repeat_handling_strategy: str,
    preserve_url_slugs: bool,
    composition_level: str,
    forward_source_to_target: bool,
) -> None:
    """
    Import multiple legacy courses or libraries into a single V2 library.

    This task performs the same logical steps as `migrate_from_modulestore`, but allows
    batching several migrations together under **one single user task** (`UserTaskStatus`).

    Unlike running `migrate_from_modulestore` in a loop (which would create multiple
    independent Celery tasks and separate statuses), the bulk migration maintains
    **one unified status record** that tracks progress across all included sources.
    This simplifies monitoring, since the client only needs to observe one task state.

    Each source item (course or library) still creates its own `ModulestoreMigration`
    database record, but all of them share the same parent task (`UserTaskStatus`).
    If any sub-migration fails (for example, due to invalid OLX or missing assets),
    the bulk migration **marks the entire task as failed** — there is no partial success.

    Args:
        self (_BulkMigrationTask):
            The Celery task instance that wraps the user task logic.
        user_id (int):
            The ID of the user initiating the migration.
        sources_pks (list[int]):
            Primary keys of the legacy modulestore sources to migrate.
        target_library_key (str):
            Key of the V2 library that will receive the imported content.
        target_collection_pks (list[int | None]):
            Optional list of target collection IDs corresponding to each source.
        create_collections (bool):
            Whether to automatically create new collections when none exist.
        repeat_handling_strategy (str):
            Strategy to handle repeated imports of the same content.
        preserve_url_slugs (bool):
            Whether to preserve existing XBlock URL slugs during import.
        composition_level (str):
            Composition level at which content should be imported (e.g. course, section).
        forward_source_to_target (bool):
            Whether to forward legacy content to its migrated equivalent after import.

    See Also:
        - `migrate_from_modulestore`: Single-source migration equivalent.
        - API docs: `/api/cms/v1/migrations/bulk/` for REST behavior and responses.
    """
    # pylint: disable=too-many-statements
    # This is a large function, but breaking it up futher would probably not
    # make it any easier to understand.

    set_code_owner_attribute_from_module(__name__)
    status: UserTaskStatus = self.status

    # Validating input
    status.set_state(MigrationStep.VALIDATING_INPUT.value)
    target_collection_list: list[Collection | None] = []

    try:
        target_library_locator = LibraryLocatorV2.from_string(target_library_key)
        target_library = get_library(target_library_locator)
        if target_library.learning_package_id is None:
            raise ValueError("Target library has no associated learning package.")

        target_package = LearningPackage.objects.get(pk=target_library.learning_package_id)

        if target_collection_pks:
            for target_collection_pk in target_collection_pks:
                target_collection_list.append(
                    Collection.objects.get(pk=target_collection_pk) if target_collection_pk else None
                )
    except (ObjectDoesNotExist, InvalidKeyError, ValueError) as exc:
        status.fail(str(exc))
        return

    source_data_list: list[_MigrationSourceData] = []

    for i in range(len(sources_pks)):
        source_data = _validate_input(
            status,
            sources_pks[i],
            repeat_handling_strategy,
            preserve_url_slugs,
            composition_level,
            target_package,
            target_collection_list[i] if target_collection_list else None,
        )
        if source_data is None:
            # Fail
            return

        source_data_list.append(source_data)

    status.increment_completed_steps()

    # Cancelling old tasks
    status.set_state(MigrationStep.CANCELLING_OLD.value)
    _cancel_old_tasks(
        [x.source for x in source_data_list],
        status,
        target_package,
        [migration.id for migration in [x.migration for x in source_data_list]],
    )
    status.increment_completed_steps()

    # Loading legacy blocks
    status.set_state(MigrationStep.LOADING)
    legacy_root_list: list[XBlock] = []
    for source_data in source_data_list:
        legacy_root = _load_xblock(status, source_data.source_root_usage_key)
        if legacy_root is None:
            # Fail
            return
        legacy_root_list.append(legacy_root)
    status.increment_completed_steps()

    for i, source_pk in enumerate(sources_pks):
        source_data = source_data_list[i]

        # Start migration for `source_pk`
        # Staging legacy blocks
        status.set_state(f"{MigrationStep.STAGING.BULK_MIGRATION_PREFIX} ({source_pk}): {MigrationStep.STAGING.value}")
        staged_content = staging_api.stage_xblock_temporarily(
            block=legacy_root_list[i],
            user_id=status.user.pk,
            purpose=CONTENT_STAGING_PURPOSE_TEMPLATE.format(source_key=source_data.source.key),
        )
        source_data.migration.staged_content = staged_content
        status.increment_completed_steps()

        # Parsing OLX
        status.set_state(f"{MigrationStep.STAGING.BULK_MIGRATION_PREFIX} ({source_pk}): {MigrationStep.PARSING.value}")
        parser = etree.XMLParser(strip_cdata=False)
        try:
            root_node = etree.fromstring(staged_content.olx, parser=parser)
        except etree.ParseError as exc:
            status.fail(f"Failed to parse source OLX (from staged content with id = {staged_content.id}): {exc}")
        status.increment_completed_steps()

        # Importing assets
        status.set_state(
            f"{MigrationStep.STAGING.BULK_MIGRATION_PREFIX} ({source_pk}): {MigrationStep.IMPORTING_ASSETS.value}"
        )
        content_by_filename = _import_assets(source_data.migration)
        status.increment_completed_steps()

        # Importing structure of the legacy block
        status.set_state(
            f"{MigrationStep.STAGING.BULK_MIGRATION_PREFIX} ({source_pk}): {MigrationStep.IMPORTING_STRUCTURE.value}"
        )
        change_log, root_migrated_node = _import_structure(
            source_data.migration,
            source_data,
            target_library,
            content_by_filename,
            root_node,
            status,
        )
        source_data.migration.change_log = change_log
        status.increment_completed_steps()

        status.set_state(
            f"{MigrationStep.STAGING.BULK_MIGRATION_PREFIX} ({source_pk}): {MigrationStep.UNSTAGING.value}"
        )
        staged_content.delete()
        status.increment_completed_steps()

        _create_migration_artifacts_incrementally(
            root_migrated_node=root_migrated_node,
            source=source_data.source,
            migration=source_data.migration,
            status=status,
            source_pk=source_pk,
        )
        status.increment_completed_steps()

    # Forwarding legacy content to migrated content
    status.set_state(MigrationStep.FORWARDING.value)
    if forward_source_to_target:
        for source_data in source_data_list:
            _forwarding_content(source_data)
    status.increment_completed_steps()

    # Populating collections
    status.set_state(MigrationStep.POPULATING_COLLECTION.value)

    # Used to check if the source has a previous migration in a V2 library collection
    # It is placed here to avoid the circular import
    from .api import get_migration_info
    for i, source_data in enumerate(source_data_list):
        migration = source_data.migration

        title = legacy_root_list[i].display_name
        if migration.target_collection is None:
            if not create_collections:
                continue

            source_key = source_data.source.key

            if migration.repeat_handling_strategy == RepeatHandlingStrategy.Fork.value:
                # Create a new collection when it is Fork
                migration.target_collection = _create_collection(target_library_locator, title)
            else:
                # It is Skip or Update
                # We need to verify if there is a previous migration with collection
                # TODO: This only fetches the latest migration, if different migrations have been done
                # on different V2 libraries, this could break the logic.
                previous_migration = get_migration_info([source_key])
                if (
                    source_key in previous_migration
                    and previous_migration[source_key].migrations__target_collection__key
                ):
                    # Has previous migration with collection
                    try:
                        # Get the previous collection
                        previous_collection = authoring_api.get_collection(
                            target_package.id,
                            previous_migration[source_key].migrations__target_collection__key,
                        )

                        migration.target_collection = previous_collection
                    except Collection.DoesNotExist:
                        # The collection no longer exists or is being migrated to a different library.
                        # In that case, create a new collection independent of strategy
                        migration.target_collection = _create_collection(target_library_locator, title)
                else:
                    # Create collection and save in migration
                    migration.target_collection = _create_collection(target_library_locator, title)

        _populate_collection(user_id, migration)

    ModulestoreMigration.objects.bulk_update(
        [x.migration for x in source_data_list],
        ["target_collection"],
    )
    status.increment_completed_steps()


@dataclass(frozen=True)
class _MigratedNode:
    """
    A node in the source tree, its target (if migrated), and any migrated children.

    Note that target_version can equal None even when there migrated children.
    This happens, particularly, if the node is above the requested composition level
    but has descendents which are at or below that level.
    """
    source_to_target: tuple[UsageKey, PublishableEntityVersion] | None
    children: list[_MigratedNode]

    def all_source_to_target_pairs(self) -> t.Iterable[tuple[UsageKey, PublishableEntityVersion]]:
        """
        Get all source_key->target_ver pairs via a pre-order traversal.
        """
        if self.source_to_target:
            yield self.source_to_target
        for child in self.children:
            yield from child.all_source_to_target_pairs()


def _migrate_node(
    *,
    context: _MigrationContext,
    source_node: XmlTree,
) -> _MigratedNode:
    """
    Migrate an OLX node (source_node) from a legacy course or library (context.source_context_key)
    to a learning package (context.target_library). If the node is a container, create it in the
    target if it is at or above the requested composition_level; otherwise, just import its contents.
    Recursively apply the same logic to all children.
    """
    # The OLX tag will map to one of the following...
    #   * A wiki tag                  --> Ignore
    #   * A recognized container type --> Migrate children, and import container if requested.
    #   * A legacy library root       --> Migrate children, but NOT the root itself.
    #   * A course root               --> Migrate children, but NOT the root itself (for Ulmo, at least. Future
    #                                     releases may support treating the Course as an importable container).
    #   * Something else              --> Try to import it as a component. If that fails, then it's either an un-
    #                                     supported component type, or it's an XBlock with dynamic children, which we
    #                                     do not support in libraries as of Ulmo.
    should_migrate_node: bool
    should_migrate_children: bool
    container_type: ContainerType | None  # if None, it's a Component
    if source_node.tag == "wiki":
        return _MigratedNode(None, [])
    try:
        container_type = ContainerType.from_source_olx_tag(source_node.tag)
    except ValueError:
        container_type = None
        if source_node.tag in {"course", "library"}:
            should_migrate_node = False
            should_migrate_children = True
        else:
            should_migrate_node = True
            should_migrate_children = False
    else:
        node_level = CompositionLevel(container_type.value)
        should_migrate_node = not node_level.is_higher_than(context.composition_level)
        should_migrate_children = True
    migrated_children: list[_MigratedNode] = []
    if should_migrate_children:
        migrated_children = [
            _migrate_node(
                context=context,
                source_node=source_node_child,
            )
            for source_node_child in source_node.getchildren()
        ]
    source_to_target: tuple[UsageKey, PublishableEntityVersion] | None = None
    if should_migrate_node:
        source_olx = etree.tostring(source_node).decode('utf-8')
        if source_block_id := source_node.get('url_name'):
            source_key: UsageKey = context.source_context_key.make_usage_key(source_node.tag, source_block_id)
            title = source_node.get('display_name', source_block_id)
            target_entity_version = (
                _migrate_container(
                    context=context,
                    source_key=source_key,
                    container_type=container_type,
                    title=title,
                    children=[
                        migrated_child.source_to_target[1]
                        for migrated_child in migrated_children if
                        migrated_child.source_to_target
                    ],
                )
                if container_type else
                _migrate_component(
                    context=context,
                    source_key=source_key,
                    olx=source_olx,
                    title=title,
                )
            )
            if target_entity_version:
                source_to_target = (source_key, target_entity_version)
                context.add_migration(source_key, target_entity_version.entity)
        else:
            log.warning(
                f"Cannot migrate node from {context.source_context_key} to {context.target_library_key} "
                f"because it lacks an url_name and thus has no identity: {source_olx}"
            )
    return _MigratedNode(source_to_target=source_to_target, children=migrated_children)


def _migrate_container(
    *,
    context: _MigrationContext,
    source_key: UsageKey,
    container_type: ContainerType,
    title: str,
    children: list[PublishableEntityVersion],
) -> PublishableEntityVersion:
    """
    Create, update, or replace a container in a library based on a source key and children.

    (We assume that the destination is a library rather than some other future kind of learning
     package, but let's keep than an internal assumption.)
    """
    target_key = _get_distinct_target_container_key(
        context,
        source_key,
        container_type,
        title,
    )
    try:
        container = libraries_api.get_container(target_key)
        container_exists = True
    except libraries_api.ContentLibraryContainerNotFound:
        container_exists = False
        if PublishableEntity.objects.filter(
            learning_package_id=context.target_package_id,
            key=target_key.container_id,
        ).exists():
            libraries_api.restore_container(container_key=target_key)
            container = libraries_api.get_container(target_key)
        else:
            container = libraries_api.create_container(
                library_key=context.target_library_key,
                container_type=container_type,
                slug=target_key.container_id,
                title=title,
                created=context.created_at,
                user_id=context.created_by,
            )
    if container_exists and context.should_skip_strategy:
        return PublishableEntityVersion.objects.get(
            entity_id=container.container_pk,
            version_num=container.draft_version_num,
        )
    return authoring_api.create_next_container_version(
        container.container_pk,
        title=title,
        entity_rows=[
            authoring_api.ContainerEntityRow(entity_pk=child.entity_id, version_pk=None)
            for child in children
        ],
        created=context.created_at,
        created_by=context.created_by,
        container_version_cls=container_type.container_model_classes[1],
    ).publishable_entity_version


def _migrate_component(
    *,
    context: _MigrationContext,
    source_key: UsageKey,
    olx: str,
    title: str,
) -> PublishableEntityVersion | None:
    """
    Create, update, or replace a component in a library based on a source key and OLX.

    (We assume that the destination is a library rather than some other future kind of learning
     package, but let's keep than an internal assumption.)
    """
    component_type = authoring_api.get_or_create_component_type("xblock.v1", source_key.block_type)

    target_key = _get_distinct_target_usage_key(
        context,
        source_key,
        component_type,
        title,
    )

    try:
        component = authoring_api.get_components(context.target_package_id).get(
            component_type=component_type,
            local_key=target_key.block_id,
        )
        component_existed = True
        # Do we have a specific method for this?
        component_deleted = not component.versioning.draft
    except Component.DoesNotExist:
        component_existed = False
        component_deleted = False
        try:
            libraries_api.validate_can_add_block_to_library(
                context.target_library_key, target_key.block_type, target_key.block_id
            )
        except libraries_api.IncompatibleTypesError as e:
            log.error(f"Error validating block for library {context.target_library_key}: {e}")
            return None
        component = authoring_api.create_component(
            context.target_package_id,
            component_type=component_type,
            local_key=target_key.block_id,
            created=context.created_at,
            created_by=context.created_by,
        )

    # Component existed and we do not replace it and it is not deleted previously
    if component_existed and not component_deleted and context.should_skip_strategy:
        return component.versioning.draft.publishable_entity_version

    # If component existed and was deleted or we have to replace the current version
    # Create the new component version for it
    component_version = libraries_api.set_library_block_olx(target_key, new_olx_str=olx)
    for filename, content_pk in context.content_by_filename.items():
        filename_no_ext, _ = os.path.splitext(filename)
        if filename_no_ext not in olx:
            continue
        new_path = f"static/{filename}"
        authoring_api.create_component_version_content(
            component_version.pk, content_pk, key=new_path
        )
    return component_version.publishable_entity_version


def _get_distinct_target_container_key(
    context: _MigrationContext,
    source_key: UsageKey,
    container_type: ContainerType,
    title: str,
) -> LibraryContainerLocator:
    """
    Find a unique key for block_id by appending a unique identifier if necessary.

    Args:
        context (_MigrationContext): The migration context.
        source_key (UsageKey): The source key.
        container_type (ContainerType): The container type.
        title (str): The title.

    Returns:
        LibraryContainerLocator: The target container key.
    """
    # Check if we already processed this block and we are not forking. If we are forking, we will
    # want a new target key.
    if context.is_already_migrated(source_key) and not context.should_fork_strategy:
        existing_version = context.get_existing_target(source_key)

        return LibraryContainerLocator(
            context.target_library_key,
            container_type.value,
            existing_version.key
        )
    # Generate new unique block ID
    base_slug = (
        source_key.block_id
        if context.preserve_url_slugs
        else (slugify(title) or source_key.block_id)
    )
    unique_slug = _find_unique_slug(context, base_slug)

    return LibraryContainerLocator(
        context.target_library_key,
        container_type.value,
        unique_slug
    )


def _get_distinct_target_usage_key(
    context: _MigrationContext,
    source_key: UsageKey,
    component_type: ComponentType,
    title: str,
) -> LibraryUsageLocatorV2:
    """
    Find a unique key for block_id by appending a unique identifier if necessary.

    Args:
        context: The migration context
        source_key: The original usage key from the source
        component_type: The component type string
        olx: The OLX content of the component

    Returns:
        A unique LibraryUsageLocatorV2 for the target

    Raises:
        ValueError: If source_key is invalid
    """
    # Check if we already processed this block and we are not forking. If we are forking, we will
    # want a new target key.
    if context.is_already_migrated(source_key) and not context.should_fork_strategy:
        log.debug(f"Block {source_key} already exists, reusing first existing target")
        existing_target = context.get_existing_target(source_key)
        block_id = existing_target.component.local_key

        # mypy thinks LibraryUsageLocatorV2 is abstract. It's not.
        return LibraryUsageLocatorV2(  # type: ignore[abstract]
            context.target_library_key,
            source_key.block_type,
            block_id
        )

    # Generate new unique block ID
    base_slug = (
        source_key.block_id
        if context.preserve_url_slugs
        else (slugify(title) or source_key.block_id)
    )
    unique_slug = _find_unique_slug(context, base_slug, component_type)

    # mypy thinks LibraryUsageLocatorV2 is abstract. It's not.
    return LibraryUsageLocatorV2(  # type: ignore[abstract]
        context.target_library_key,
        source_key.block_type,
        unique_slug
    )


def _find_unique_slug(
    context: _MigrationContext,
    base_slug: str,
    component_type: ComponentType | None = None,
    max_attempts: int = 1000
) -> str:
    """
    Find a unique slug by appending incrementing numbers if necessary.
    Using batch querying to avoid multiple database roundtrips.

    Args:
        component_type: The component type to check against
        base_slug: The base slug to make unique
        max_attempts: Maximum number of attempts to prevent infinite loops

    Returns:
        A unique slug string

    Raises:
        RuntimeError: If unable to find unique slug within max_attempts
    """
    if not component_type:
        base_key = base_slug
    else:
        base_key = f"{component_type}:{base_slug}"

    existing_publishable_entity_keys = context.get_existing_target_entity_keys(base_key)

    # Check if base slug is available
    if base_key not in existing_publishable_entity_keys:
        return base_slug

    # Try numbered variations until we find one that doesn't exist
    for i in range(1, max_attempts + 1):
        candidate_slug = f"{base_slug}_{i}"
        candidate_key = f"{component_type}:{candidate_slug}" if component_type else candidate_slug

        if candidate_key not in existing_publishable_entity_keys:
            return candidate_slug

    raise RuntimeError(f"Unable to find unique slug after {max_attempts} attempts for base: {base_slug}")


def _create_migration_artifacts_incrementally(
    root_migrated_node: _MigratedNode,
    source: ModulestoreSource,
    migration: ModulestoreMigration,
    status: UserTaskStatus,
    source_pk: int | None = None,
) -> None:
    """
    Create ModulestoreBlockSource and ModulestoreBlockMigration objects incrementally.
    """
    nodes = tuple(root_migrated_node.all_source_to_target_pairs())
    total_nodes = len(nodes)
    processed = 0

    for source_usage_key, target_version in root_migrated_node.all_source_to_target_pairs():
        block_source, _ = ModulestoreBlockSource.objects.get_or_create(
            overall_source=source,
            key=source_usage_key
        )

        ModulestoreBlockMigration.objects.create(
            overall_migration=migration,
            source=block_source,
            target_id=target_version.entity_id,
        )

        processed += 1
        if processed % 10 == 0 or processed == total_nodes:
            if source_pk:
                status.set_state(
                    f"{MigrationStep.STAGING.BULK_MIGRATION_PREFIX} ({source_pk}): "
                    f"{MigrationStep.MAPPING_OLD_TO_NEW.value} ({processed}/{total_nodes})"
                )
            else:
                status.set_state(
                    f"{MigrationStep.MAPPING_OLD_TO_NEW.value} ({processed}/{total_nodes})"
                )
