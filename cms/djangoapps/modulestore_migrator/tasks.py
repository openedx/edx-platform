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
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from edx_django_utils.monitoring import set_code_owner_attribute_from_module
from lxml import etree
from lxml.etree import _ElementTree as XmlTree
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import (
    CourseLocator, LibraryLocator,
    LibraryLocatorV2, LibraryUsageLocatorV2, LibraryContainerLocator
)
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import (
    Collection,
    Component,
    ContainerVersion,
    LearningPackage,
    PublishableEntity,
    PublishableEntityVersion,
)
from user_tasks.tasks import UserTask, UserTaskStatus

from openedx.core.djangoapps.content_libraries.api import ContainerType
from openedx.core.djangoapps.content_libraries import api as libraries_api
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.djangoapps.content_staging import api as staging_api
from xmodule.modulestore import exceptions as modulestore_exceptions
from xmodule.modulestore.django import modulestore

from .constants import CONTENT_STAGING_PURPOSE_TEMPLATE
from .data import CompositionLevel
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


@shared_task(base=_MigrationTask, bind=True)
# Note: The decorator @set_code_owner_attribute cannot be used here because the UserTaskMixin
#   does stack inspection and can't handle additional decorators.
def migrate_from_modulestore(
    self: _MigrationTask,
    *,
    user_id: int,
    source_pk: int,
    target_package_pk: int,
    target_collection_pk: int,
    replace_existing: bool,
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
        target_library = ContentLibrary.objects.get(learning_package_id=target_package_pk)
        target_collection = Collection.objects.get(pk=target_collection_pk) if target_collection_pk else None
    except ObjectDoesNotExist as exc:
        status.fail(str(exc))
        return
    if isinstance(source.key, CourseLocator):
        source_root_usage_key = source.key.make_usage_key('course', 'course')
    elif isinstance(source.key, LibraryLocator):
        source_root_usage_key = source.key.make_usage_key('library', 'library')
    else:
        status.fail(
            f"Not a valid source context key: {source.key}. "
            "Source key must reference a course or a legacy library."
        )
        return
    migration = ModulestoreMigration.objects.create(
        source=source,
        composition_level=composition_level,
        replace_existing=replace_existing,
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
    with authoring_api.bulk_draft_changes_for(migration.target.id) as change_log:
        root_migrated_node = _migrate_node(
            content_by_filename=content_by_filename,
            source_context_key=source_root_usage_key.course_key,
            source_node=root_node,
            target_library_key=target_library.library_key,
            target_package_id=target_package_pk,
            replace_existing=replace_existing,
            composition_level=CompositionLevel(composition_level),
            created_at=datetime.now(timezone.utc),
            created_by=status.user_id,
        )
    migration.change_log = change_log
    status.increment_completed_steps()

    status.set_state(MigrationStep.UNSTAGING.value)
    staged_content.delete()
    status.increment_completed_steps()

    # @@TODO We currently do the mapping in bulk in order to reduce the number of DB queries.
    #        But, as a user, it means that there are no artifacts (ModulestoreBlockMigrations)
    #        to be shown as the structure is being imported, which takes can take several minutes.
    #        Would be better to, instead, create each ModulestoreBlockSource and
    #        ModulestoreBlockMigration as we create its PublisahbleEntity(Version)? If
    #        we did this, we'd want to make sure that the objects are actually visible
    #        to the user mid-import (via django admin, or the library interface, or even just as
    #        as a "progress bar" field in the REST API), otherwise this would be pointless.
    status.set_state(MigrationStep.MAPPING_OLD_TO_NEW.value)
    block_source_keys_to_target_vers = dict(root_migrated_node.all_source_to_target_pairs())
    ModulestoreBlockSource.objects.bulk_create(
        [
            ModulestoreBlockSource(overall_source=source, key=source_usage_key)
            for source_usage_key in block_source_keys_to_target_vers.keys()
        ],
        # Note: bulk_create will *not* return the primary keys of ModulestoreBlockSource
        # objects that already exist (and thus were skipped by ignore_conflicts), so, in
        # order to use ModulestoreBlockSource instances, we must re-load them in the next step.
        ignore_conflicts=True
    )
    block_source_keys_to_sources: dict[UsageKey, ModulestoreBlockSource] = {
        block_source.key: block_source for block_source in source.blocks.all()
    }
    # @@TODO We get an error when we try to use the change_log, because it hasn't
    #        been saved yet. Until we fix this, we won't be able to set
    #        ModuleBlockMigration.change_log_record.
    # block_target_pks_to_change_log_record_pks: dict[int, int] = dict(
    #     change_log.records.values_list("target_entity_id", "id")
    # )
    #block_migrations = ModulestoreBlockMigration.objects.bulk_create(
    ModulestoreBlockMigration.objects.bulk_create(
        [
            ModulestoreBlockMigration(
                overall_migration=migration,
                source=block_source_keys_to_sources[block_source_key],
                target_id=block_target_ver.entity_id,
                # @@TODO See above
                # change_log_record_id=block_target_pks_to_change_log_record_pks[block_target_ver.entity_id],
            )
            for block_source_key, block_target_ver in block_source_keys_to_target_vers.items()
        ],
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
        # ModulestoreBlockSource.objects.bulk_update(block_sources_to_block_migrations.keys(), ["forwarded"])
        source.forwarded = migration
        source.save()
    status.increment_completed_steps()

    status.set_state(MigrationStep.POPULATING_COLLECTION.value)
    if target_collection:
        # @@TODO This dict (block_target_pks_to_change_log_record_pks) was based on the change_log calculation
        #        above which is commented out. In order to add to target_collection, we either need to fix the
        #        change_log query above, or we need to calculate these target_pks some other way
        block_target_pks: list[int] = []  # list(block_target_pks_to_change_log_record_pks.keys())
        authoring_api.add_to_collection(
            learning_package_id=target_package_pk,
            key=target_collection.key,
            entities_qset=PublishableEntity.objects.filter(id__in=block_target_pks),
            created_by=user_id,
        )
    status.increment_completed_steps()


@dataclass(frozen=True)
class _MigratedNode:
    """
    A node in the source tree, its target (if migrated), and any migrated children.

    Note that target_version can equal None even when there migrated children.
    This happens, particularly, if the node is above the requested composition level
    but has descendents which are at or below sad level.
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
    content_by_filename: dict[str, int],
    source_context_key: CourseKey,  # Note: This includes legacy LibraryLocators, which are sneakily CourseKeys.
    source_node: XmlTree,
    target_package_id: int,
    target_library_key: LibraryLocatorV2,
    composition_level: CompositionLevel,
    replace_existing: bool,
    created_at: datetime,
    created_by: int,
) -> _MigratedNode:
    """
    Migration an OLX node (source_node) from a legacy course or library (source_context_key) to a
    learning package (target_library). If the node is a container, create it in the target iff
    it is at or above the requested composition_level; otherwise, just import its contents.
    Recursively apply the same logic to all children.
    """
    # The OLX tag will map to one of the following...
    #   * A wiki tag                  --> Ignore
    #   * A recognized container type --> Migration children, and import container if requested.
    #   * A legacy library root       --> Migration children, but NOT the root itself.
    #   * A course root               --> Migration children, but NOT the root itself (for Teak, at least. Future
    #                                     releases may support treating the Course as an importable container).
    #   * Something else              --> Try to import it as a component. If that fails, then it's either an un-
    #                                     supported component type, or it's an XBlock with dynamic children, which we
    #                                     do not support in libraries as of Teak.
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
        should_migrate_node = not node_level.is_higher_than(composition_level)
        should_migrate_children = True
    migrated_children: list[_MigratedNode] = []
    if should_migrate_children:
        migrated_children = [
            _migrate_node(
                content_by_filename=content_by_filename,
                source_context_key=source_context_key,
                source_node=source_node_child,
                target_package_id=target_package_id,
                target_library_key=target_library_key,
                composition_level=composition_level,
                replace_existing=replace_existing,
                created_by=created_by,
                created_at=created_at,
            )
            for source_node_child in source_node.getchildren()
        ]
    source_to_target: tuple[UsageKey, PublishableEntityVersion] | None = None
    if should_migrate_node:
        source_olx = etree.tostring(source_node).decode('utf-8')
        if source_block_id := source_node.get('url_name'):
            source_key: UsageKey = source_context_key.make_usage_key(source_node.tag, source_block_id)
            target_entity_version = (
                _migrate_container(
                    source_key=source_key,
                    container_type=container_type,
                    title=source_node.get('display_name', source_block_id),
                    children=[
                        migrated_child.source_to_target[1]
                        for migrated_child in migrated_children if
                        migrated_child.source_to_target
                    ],
                    target_library_key=target_library_key,
                    replace_existing=replace_existing,
                    created_by=created_by,
                    created_at=created_at,
                )
                if container_type else
                _migrate_component(
                    content_by_filename=content_by_filename,
                    source_key=source_key,
                    olx=source_olx,
                    target_package_id=target_package_id,
                    target_library_key=target_library_key,
                    replace_existing=replace_existing,
                    created_by=created_by,
                    created_at=created_at,
                )
            )
            if target_entity_version:
                source_to_target = (source_key, target_entity_version)
        else:
            log.warning(
                f"Cannot migrate node from {source_context_key} to {target_library_key} "
                f"because it lacks an url_name and thus has no identity: {source_olx}"
            )
    return _MigratedNode(source_to_target=source_to_target, children=migrated_children)


def _migrate_container(
    *,
    source_key: UsageKey,
    container_type: ContainerType,
    title: str,
    children: list[PublishableEntityVersion],
    target_library_key: LibraryLocatorV2,
    replace_existing: bool,
    created_by: int,
    created_at: datetime,
) -> PublishableEntityVersion:
    """
    Create, update, or replace a container in a library based on a source key and children.

    (We assume that the destination is a library rather than some other future kind of learning
     package, but let's keep than an internal assumption.)
    """
    target_key = LibraryContainerLocator(
        target_library_key, container_type.value, _slugify_source_usage_key(source_key)
    )
    try:
        container = libraries_api.get_container(target_key)
        container_exists = True
    except libraries_api.ContentLibraryContainerNotFound:
        container_exists = False
        container = libraries_api.create_container(
            library_key=target_library_key,
            container_type=container_type,
            slug=target_key.container_id,
            title=title,
            created=created_at,
            user_id=created_by,
        )
    if container_exists and not replace_existing:
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
        created=created_at,
        created_by=created_by,
        container_version_cls=container_type.container_model_classes[1],
    ).publishable_entity_version


def _migrate_component(
    *,
    content_by_filename: dict[str, int],
    source_key: UsageKey,
    olx: str,
    target_package_id: int,
    target_library_key: LibraryLocatorV2,
    replace_existing: bool,
    created_by: int,
    created_at: datetime,
) -> PublishableEntityVersion | None:
    """
    Create, update, or replace a component in a library based on a source key and OLX.

    (We assume that the destination is a library rather than some other future kind of learning
     package, but let's keep than an internal assumption.)
    """
    component_type = authoring_api.get_or_create_component_type("xblock.v1", source_key.block_type)
    # mypy thinks LibraryUsageLocatorV2 is abstract. It's not.
    target_key = LibraryUsageLocatorV2(  # type: ignore[abstract]
        target_library_key, source_key.block_type, _slugify_source_usage_key(source_key)
    )
    try:
        component = authoring_api.get_components(target_package_id).get(
            component_type=component_type,
            local_key=target_key.block_id,
        )
        component_existed = True
    except Component.DoesNotExist:
        component_existed = False
        try:
            libraries_api.validate_can_add_block_to_library(
                target_library_key, target_key.block_type, target_key.block_id
            )
        except libraries_api.IncompatibleTypesError as e:
            log.error(f"Error validating block for library {target_library_key}: {e}")
            return None
        component = authoring_api.create_component(
            target_package_id,
            component_type=component_type,
            local_key=target_key.block_id,
            created=created_at,
            created_by=created_by,
        )
    if component_existed and not replace_existing:
        return component.versioning.draft.publishable_entity_version
    component_version = libraries_api.set_library_block_olx(target_key, new_olx_str=olx)
    for filename, content_pk in content_by_filename.items():
        filename_no_ext, _ = os.path.splitext(filename)
        if filename_no_ext not in olx:
            continue
        new_path = f"static/{filename}"
        try:
            authoring_api.create_component_version_content(component_version.pk, content_pk, key=new_path)
        # @@TODO is there a way to determine content already exists that doesn't run the risk
        #        of swallowing other, unexpected IntegrityErrors?
        except IntegrityError:
            pass  # Content already exists
    return component_version.publishable_entity_version


def _slugify_source_usage_key(key: UsageKey) -> str:
    """
    Return an appropriate slug (aka block_id, aka container_id) for the target entity.

    Mix the legacy source context (course/library) information with the source block_id,
    thus ensuring that migrations of two blocks with the same id from different source
    contexts will not collide.

    Note: We don't need to factor in block_type, because the target keys already do that.
    Note: Slugs can't have plus signs, which are normally how legacy keys are delimted.

    @@TODO -- Is this good enough? Conflicts are technically possible if a user has manually
    formatted the key this way, but that seems super unlikely to happen by accident, right ... ?
    Conflicts are also technically posssible for
    """
    context_key = key.course_key
    if isinstance(context_key, LibraryLocator):
        return f"{context_key.org}__{context_key.library}__{key.block_id}"
    elif isinstance(context_key, CourseKey):
        return f"{context_key.org}__{context_key.course}__{context_key.run}__{key.block_id}"
    else:
        raise ValueError(
            f"Unexpected source usage key: {key}. Expected legacy course or library usage locator."
        )
