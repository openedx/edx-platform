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

from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify
from edx_django_utils.monitoring import set_code_owner_attribute_from_module
from lxml import etree
from lxml.etree import _ElementTree as XmlTree
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import (
    CourseLocator, LibraryLocator,
    LibraryLocatorV2, LibraryUsageLocatorV2, LibraryContainerLocator
)
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import (
    Collection,
    Component,
    ComponentType,
    LearningPackage,
    PublishableEntity,
    PublishableEntityVersion,
)
from user_tasks.tasks import UserTask, UserTaskStatus

from openedx.core.djangoapps.content_libraries.api import ContainerType, get_library
from openedx.core.djangoapps.content_libraries import api as libraries_api
from openedx.core.djangoapps.content_staging import api as staging_api
from xmodule.modulestore import exceptions as modulestore_exceptions
from xmodule.modulestore.django import modulestore
from common.djangoapps.split_modulestore_django.models import SplitModulestoreCourseIndex

from .constants import CONTENT_STAGING_PURPOSE_TEMPLATE
from .data import CompositionLevel, RepeatHandlingStrategy
from .models import ModulestoreSource, ModulestoreMigration, ModulestoreBlockSource, ModulestoreBlockMigration


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


class _MigrationTask(UserTask):
    """
    Base class for migrate_to_modulestore
    """

    @staticmethod
    def calculate_total_steps(arguments_dict):
        """
        Get number of in-progress steps in importing process, as shown in the UI.
        """
        return len(list(MigrationStep))


@dataclass(frozen=True)
class _MigrationContext:
    """
    Context for the migration process.
    """
    existing_source_to_target_keys: dict[  # Note: It's intended to be mutable to reflect changes during migration.
        UsageKey, PublishableEntity
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
        return self.existing_source_to_target_keys[source_key]

    def add_migration(self, source_key: UsageKey, target: PublishableEntity) -> None:
        """Update the context with a new migration (keeps it current)"""
        self.existing_source_to_target_keys[source_key] = target

    def get_existing_target_entity_keys(self, base_key: str) -> set[str]:
        return set(
            publishable_entity.key for _, publishable_entity in
            self.existing_source_to_target_keys.items()
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


@shared_task(base=_MigrationTask, bind=True)
# Note: The decorator @set_code_owner_attribute cannot be used here because the UserTaskMixin
#   does stack inspection and can't handle additional decorators.
def migrate_from_modulestore(
    self: _MigrationTask,
    *,
    user_id: int,
    source_pk: int,
    target_package_pk: int,
    target_library_key: str,
    target_collection_pk: int,
    repeat_handling_strategy: str,
    preserve_url_slugs: bool,
    composition_level: str,
    forward_source_to_target: bool,
) -> None:
    """
    Import a course or legacy library into a learning package.

    Currently, the target learning package must be associated with a V2 content library, but that
    restriction may be loosened in the future as more types of learning packages are developed.
    """
    # pylint: disable=too-many-statements
    # This is a large function, but breaking it up futher would probably not
    # make it any easier to understand.

    set_code_owner_attribute_from_module(__name__)

    status: UserTaskStatus = self.status
    status.set_state(MigrationStep.VALIDATING_INPUT.value)
    try:
        source = ModulestoreSource.objects.get(pk=source_pk)
        target_package = LearningPackage.objects.get(pk=target_package_pk)
        target_library = get_library(LibraryLocatorV2.from_string(target_library_key))
        target_collection = Collection.objects.get(pk=target_collection_pk) if target_collection_pk else None
    except (ObjectDoesNotExist, InvalidKeyError) as exc:
        status.fail(str(exc))
        return

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
        return

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
    status.increment_completed_steps()

    status.set_state(MigrationStep.CANCELLING_OLD.value)
    # In order to prevent a user from accidentally starting a bunch of identical import tasks...
    migrations_to_cancel = ModulestoreMigration.objects.filter(
        # get all Migration tasks by this user with the same source and target
        task_status__user=status.user,
        source=source,
        target=target_package,
    ).select_related('task_status').exclude(
        # (excluding that aren't running)
        task_status__state__in=(UserTaskStatus.CANCELED, UserTaskStatus.FAILED, UserTaskStatus.SUCCEEDED)
    ).exclude(
        # (excluding this migration itself)
        id=migration.id
    )
    # ... and cancel their tasks and clean away their staged content.
    for migration_to_cancel in migrations_to_cancel:
        if migration_to_cancel.task_status:
            migration_to_cancel.task_status.cancel()
        if migration_to_cancel.staged_content:
            migration_to_cancel.staged_content.delete()
    status.increment_completed_steps()

    status.set_state(MigrationStep.LOADING)
    try:
        legacy_root = modulestore().get_item(source_root_usage_key)
    except modulestore_exceptions.ItemNotFoundError as exc:
        status.fail(f"Failed to load source item '{source_root_usage_key}' from ModuleStore: {exc}")
        return
    if not legacy_root:
        status.fail(f"Could not find source item '{source_root_usage_key}' in ModuleStore")
        return
    status.increment_completed_steps()

    status.set_state(MigrationStep.STAGING.value)
    staged_content = staging_api.stage_xblock_temporarily(
        block=legacy_root,
        user_id=status.user.pk,
        purpose=CONTENT_STAGING_PURPOSE_TEMPLATE.format(source_key=source.key),
    )
    migration.staged_content = staged_content
    status.increment_completed_steps()

    status.set_state(MigrationStep.PARSING.value)
    parser = etree.XMLParser(strip_cdata=False)
    try:
        root_node = etree.fromstring(staged_content.olx, parser=parser)
    except etree.ParseError as exc:
        status.fail(f"Failed to parse source OLX (from staged content with id = {staged_content.id}): {exc}")
    status.increment_completed_steps()

    status.set_state(MigrationStep.IMPORTING_ASSETS.value)
    content_by_filename: dict[str, int] = {}
    now = datetime.now(tz=timezone.utc)
    for staged_content_file_data in staging_api.get_staged_content_static_files(staged_content.id):
        old_path = staged_content_file_data.filename
        file_data = staging_api.get_staged_content_static_file_data(staged_content.id, old_path)
        if not file_data:
            log.error(
                f"Staged content {staged_content.id} included referenced file {old_path}, "
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
    status.increment_completed_steps()

    status.set_state(MigrationStep.IMPORTING_STRUCTURE.value)

    # "key" is locally unique across all PublishableEntities within
    # a given LearningPackage.
    # We use this mapping to ensure that we don't create duplicate
    # PublishableEntities during the migration process for a given LearningPackage.
    existing_source_to_target_keys = {
        block.source.key: block.target for block in ModulestoreBlockMigration.objects.filter(
            overall_migration__target=migration.target.id
        )
    }

    migration_context = _MigrationContext(
        existing_source_to_target_keys=existing_source_to_target_keys,
        target_package_id=target_package_pk,
        target_library_key=target_library.key,
        source_context_key=source_root_usage_key.course_key,
        content_by_filename=content_by_filename,
        composition_level=CompositionLevel(composition_level),
        repeat_handling_strategy=RepeatHandlingStrategy(repeat_handling_strategy),
        preserve_url_slugs=preserve_url_slugs,
        created_by=status.user_id,
        created_at=datetime.now(timezone.utc),
    )

    with authoring_api.bulk_draft_changes_for(migration.target.id) as change_log:
        root_migrated_node = _migrate_node(
            context=migration_context,
            source_node=root_node,
        )
    change_log.save()
    migration.change_log = change_log
    status.increment_completed_steps()

    status.set_state(MigrationStep.UNSTAGING.value)
    staged_content.delete()
    status.increment_completed_steps()

    _create_migration_artifacts_incrementally(
        root_migrated_node=root_migrated_node,
        source=source,
        migration=migration,
        status=status,
    )

    block_migrations = ModulestoreBlockMigration.objects.filter(overall_migration=migration)
    status.increment_completed_steps()

    status.set_state(MigrationStep.FORWARDING.value)
    if forward_source_to_target:
        block_sources_to_block_migrations = {
            block_migration.source: block_migration for block_migration in block_migrations
        }
        for block_source, block_migration in block_sources_to_block_migrations.items():
            block_source.forwarded = block_migration
            block_source.save()

        source.forwarded = migration
        source.save()
    status.increment_completed_steps()

    status.set_state(MigrationStep.POPULATING_COLLECTION.value)
    if target_collection:
        block_target_pks: list[int] = list(
            ModulestoreBlockMigration.objects.filter(
                overall_migration=migration
            ).values_list('target_id', flat=True)
        )
        if block_target_pks:
            authoring_api.add_to_collection(
                learning_package_id=target_package_pk,
                key=target_collection.key,
                entities_qset=PublishableEntity.objects.filter(id__in=block_target_pks),
                created_by=user_id,
            )
        else:
            log.warning("No target entities found to add to collection")
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
    # Check if we already processed this block
    if context.is_already_migrated(source_key):
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
    # Check if we already processed this block
    if context.is_already_migrated(source_key):
        log.debug(f"Block {source_key} already exists, reusing existing target")
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
    status: UserTaskStatus
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
            status.set_state(
                f"{MigrationStep.MAPPING_OLD_TO_NEW.value} ({processed}/{total_nodes})"
            )
