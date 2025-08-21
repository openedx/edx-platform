"""
Helper functions for importing course content into a library.
"""
from datetime import datetime, timezone
from functools import partial
import logging
import mimetypes
import os
import secrets
from typing import TYPE_CHECKING

from django.db import transaction
from django.db.utils import IntegrityError
from lxml import etree

from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import CourseLocator
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import Component, Container, ContainerVersion, PublishableEntity

from openedx.core.djangoapps.content_libraries import api
from openedx.core.djangoapps.content_staging import api as content_staging_api
from xmodule.modulestore.django import modulestore

from .data import CompositionLevel, ImportStatus, PublishableVersionWithMapping
from .models import Import, PublishableEntityMapping

if TYPE_CHECKING:
    from openedx_learning.apps.authoring_models import LearningPackage
    from xblock.core import XBlock

    from openedx.core.djangoapps.content_staging.api import _StagedContent as StagedContent


log = logging.getLogger(__name__)
parser = etree.XMLParser(strip_cdata=False)


class ImportClient:
    """
    Client for importing course content into a library.

    This class handles the import of course content from staged content into a
    content library, creating the appropriate container hierarchy based on the
    specified composition level.
    """

    # The create functions have different kwarg names for the child list,
    # so we need to use partial to set the child list to empty.
    CONTAINER_CREATORS_MAP: dict[str, partial] = {
        api.ContainerType.Section.olx_tag: partial(authoring_api.create_section_and_version, subsections=[]),
        api.ContainerType.Subsection.olx_tag: partial(authoring_api.create_subsection_and_version, units=[]),
        api.ContainerType.Unit.olx_tag: partial(authoring_api.create_unit_and_version, components=[]),
    }

    CONTAINER_OVERRIDERS_MAP: dict[str, partial] = {
        api.ContainerType.Section.olx_tag: partial(authoring_api.create_next_section_version, subsections=[]),
        api.ContainerType.Subsection.olx_tag: partial(authoring_api.create_next_subsection_version, units=[]),
        api.ContainerType.Unit.olx_tag: partial(authoring_api.create_next_unit_version, components=[]),
    }

    def __init__(
        self,
        import_event: Import,
        block_usage_key_to_import: str,
        target_learning_package: 'LearningPackage',
        staged_content: 'StagedContent',
        composition_level: str,
        override: bool = False,
    ):
        self.import_event = import_event
        self.block_usage_key_to_import = block_usage_key_to_import
        self.learning_package = target_learning_package
        self.staged_content = staged_content
        self.composition_level = composition_level
        self.override = override

        self.user_id = import_event.user_id
        self.content_library = target_learning_package.contentlibrary
        self.library_key = self.content_library.library_key
        self.parser = etree.XMLParser(strip_cdata=False)

    def import_from_staged_content(self) -> list[PublishableVersionWithMapping]:
        """
        Import staged content into a library.
        """
        node = etree.fromstring(self.staged_content.olx, parser=parser)
        usage_key = UsageKey.from_string(self.block_usage_key_to_import)
        block_to_import = get_node_for_usage_key(node, usage_key)
        if block_to_import is None:
            return []

        return self._process_import(self.block_usage_key_to_import, block_to_import)

    def _process_import(self, usage_key_string, block_to_import) -> list[PublishableVersionWithMapping]:
        """
        Process import of a block from staged content into a library.

        Imports a block and its children into the library based on the
        composition level. It handles both simple and complicated blocks, creating
        the necessary container hierarchy.
        """
        usage_key = UsageKey.from_string(usage_key_string)
        result = []

        if block_to_import.tag not in CompositionLevel.OLX_COMPLEX_LEVELS.value:
            return self._import_simple_block(block_to_import, usage_key)

        for child in block_to_import.getchildren():
            child_usage_key_string = get_usage_key_string_from_staged_content(
                self.staged_content, child.get('url_name')
            )
            if not child_usage_key_string:
                continue

            result.extend(self._import_child_block(child, child_usage_key_string))

        if self.composition_level == CompositionLevel.COMPONENT.value:
            return [
                publishable_version_with_mapping for publishable_version_with_mapping in result
                if not isinstance(publishable_version_with_mapping.publishable_version, ContainerVersion)
            ]
        return result

    def _import_simple_block(self, block_to_import, usage_key) -> list[PublishableVersionWithMapping]:
        """
        Import a simple block into the library.

        Creates a block in the library from the staged content block.
        It returns a list containing the created component version.
        """
        publishable_version_with_mapping = self._create_block_in_library(block_to_import, usage_key)
        return [publishable_version_with_mapping] if publishable_version_with_mapping else []

    def _import_child_block(self, child, child_usage_key_string):
        """
        Import a child block into the library.

        Determines whether the child block is simple or complicated and
        delegates the import process to the appropriate helper method.
        """
        child_usage_key = UsageKey.from_string(child_usage_key_string)
        if child.tag in CompositionLevel.OLX_COMPLEX_LEVELS.value:
            return self._import_complicated_child(child, child_usage_key_string)
        else:
            return self._import_simple_block(child, child_usage_key)

    def _import_complicated_child(self, child, child_usage_key_string):
        """
        Import a complicated child block into the library.

        Handles the import of complicated child blocks, including creating
        containers and updating components.
        Returns a list containing the created container version.
        """
        if not self._should_create_container(child.tag):
            return self._process_import(child_usage_key_string, child)

        container_version_with_mapping = self.get_or_create_container(
            child.tag,
            child.get('url_name'),
            child.get('display_name', child.tag),
            child_usage_key_string,
        )
        child_component_versions_with_mapping = self._process_import(child_usage_key_string, child)
        child_component_versions = [
            child_component_version.publishable_version for child_component_version
            in child_component_versions_with_mapping
        ]
        self._update_container_components(container_version_with_mapping.publishable_version, child_component_versions)
        return [container_version_with_mapping] + child_component_versions_with_mapping

    def _should_create_container(self, container_type: str) -> bool:
        """
        Determine if a new container should be created.

        Container type should be at a lower level than the current composition level.
        """
        composition_hierarchy = CompositionLevel.OLX_COMPLEX_LEVELS.value
        return (
            container_type in composition_hierarchy and
            self.composition_level in composition_hierarchy and
            composition_hierarchy.index(container_type) <= composition_hierarchy.index(self.composition_level)
        )

    def get_or_create_container(
        self,
        container_type: str,
        key: str,
        display_name: str,
        block_usage_key_string: str
    ) -> PublishableVersionWithMapping:
        """
        Create a container of the specified type.

        Creates a container (e.g., chapter, sequential, vertical) in the
        content library.
        """
        try:
            container_creator_func = self.CONTAINER_CREATORS_MAP[container_type]
            container_override_func = self.CONTAINER_OVERRIDERS_MAP[container_type]
        except KeyError as exc:
            raise ValueError(f"Unknown container type: {container_type}") from exc

        try:
            container_version = self.content_library.learning_package.publishable_entities.get(key=key)
        except PublishableEntity.DoesNotExist:
            container_version = None

        if container_version and self.override:
            container_version = container_override_func(
                container_version.container,
                title=display_name or f"New {container_type}",
                created=datetime.now(tz=timezone.utc),
                created_by=self.import_event.user_id,
            )
        elif not container_version:
            _, container_version = container_creator_func(
                self.learning_package.id,
                key=key or secrets.token_hex(16),
                title=display_name or f"New {container_type}",
                created=datetime.now(tz=timezone.utc),
                created_by=self.import_event.user_id,
            )

        publishable_entity_mapping, _ = get_or_create_publishable_entity_mapping(
            block_usage_key_string,
            container_version.container
        )

        return PublishableVersionWithMapping(container_version, publishable_entity_mapping)

    def _update_container_components(self, container_version, component_versions):
        """
        Update components of a container.
        """
        entity_rows = [
            authoring_api.ContainerEntityRow(
                entity_pk=cv.container.pk if isinstance(cv, ContainerVersion) else cv.component.pk,
                version_pk=cv.pk,
            )
            for cv in component_versions
        ]
        return authoring_api.create_next_container_version(
            container_pk=container_version.container.pk,
            title=container_version.title,
            entity_rows=entity_rows,
            created=datetime.now(tz=timezone.utc),
            created_by=self.import_event.user_id,
            container_version_cls=container_version.__class__,
        )

    def _create_block_in_library(self, block_to_import, usage_key) -> PublishableVersionWithMapping | None:
        """
        Create a block in a library from a staged content block.
        """
        now = datetime.now(tz=timezone.utc)
        staged_content_files = content_staging_api.get_staged_content_static_files(self.staged_content.id)

        with transaction.atomic():
            component_type = authoring_api.get_or_create_component_type("xblock.v1", usage_key.block_type)
            does_component_exist = authoring_api.get_components(
                self.learning_package.id
            ).filter(local_key=usage_key.block_id).exists()

            if does_component_exist:
                if not self.override:
                    log.info(f"Component {usage_key.block_id} already exists in library {self.library_key}, skipping.")
                    return None
                else:
                    component_version = self._handle_component_override(usage_key, etree.tostring(block_to_import))
            else:
                try:
                    _, library_usage_key = api.validate_can_add_block_to_library(
                        self.library_key,
                        block_to_import.tag,
                        usage_key.block_id,
                    )
                except api.IncompatibleTypesError as e:
                    log.error(f"Error validating block {usage_key} for library {self.library_key}: {e}")
                    return None

                authoring_api.create_component(
                    self.learning_package.id,
                    component_type=component_type,
                    local_key=usage_key.block_id,
                    created=now,
                    created_by=self.import_event.user_id,
                )
                component_version = api.set_library_block_olx(library_usage_key, etree.tostring(block_to_import))

            self._process_staged_content_files(
                component_version,
                staged_content_files,
                usage_key,
                block_to_import,
                now,
            )
            publishable_entity_mapping, _ = get_or_create_publishable_entity_mapping(
                usage_key,
                component_version.component
            )
            return PublishableVersionWithMapping(component_version, publishable_entity_mapping)

    def _handle_component_override(self, usage_key, new_content):
        """
        Create new ComponentVersion for overridden component.
        """
        component_version = None
        try:
            component = authoring_api.get_components(self.learning_package.id).get(local_key=usage_key.block_id)
        except Component.DoesNotExist:
            return component_version
        library_usage_key = api.library_component_usage_key(self.library_key, component)

        component_version = api.set_library_block_olx(library_usage_key, new_content)

        return component_version

    def _process_staged_content_files(
        self,
        component_version,
        staged_content_files,
        usage_key,
        block_to_import,
        created_at,
    ):
        """
        Process staged content files for a component.

        Processes the staged content files for a component, creating the
        necessary file content and associating it with the component version.
        """
        block_olx = etree.tostring(block_to_import).decode('utf-8')

        for staged_content_file_data in staged_content_files:
            original_filename = staged_content_file_data.filename
            file_basename = os.path.basename(original_filename)
            file_basename_no_ext, _ = os.path.splitext(file_basename)

            # Skip files not referenced in the block
            if file_basename not in block_olx and file_basename_no_ext not in block_olx:
                log.info(f"Skipping file {original_filename} as it is not referenced in block {usage_key}")
                continue

            file_data = content_staging_api.get_staged_content_static_file_data(
                self.staged_content.id,
                original_filename,
            )
            if not file_data:
                log.error(
                    f"Staged content {self.staged_content.id} included referenced "
                    f"file {original_filename}, but no file data was found."
                )
                continue

            filename = f"static/{file_basename}"
            media_type_str, _ = mimetypes.guess_type(filename)
            if not media_type_str:
                media_type_str = "application/octet-stream"

            media_type = authoring_api.get_or_create_media_type(media_type_str)
            content = authoring_api.get_or_create_file_content(
                self.learning_package.id,
                media_type.id,
                data=file_data,
                created=created_at,
            )

            try:
                authoring_api.create_component_version_content(component_version.pk, content.id, key=filename)
            except IntegrityError:
                pass  # Content already exists


def import_from_staged_content(
    import_event: Import,
    usage_key_string: str,
    target_learning_package: 'LearningPackage',
    staged_content: 'StagedContent',
    composition_level: str,
    override: bool = False,
) -> list[PublishableVersionWithMapping]:
    """
    Import staged content to a library from staged content.

    Returns a list of PublishableVersionWithMappings created during the import.
    """
    import_client = ImportClient(
        import_event,
        usage_key_string,
        target_learning_package,
        staged_content,
        composition_level,
        override,
    )
    return import_client.import_from_staged_content()


def get_or_create_publishable_entity_mapping(usage_key, component) -> tuple[PublishableEntityMapping, bool]:
    """
    Creates a mapping between the source usage key and the target publishable entity.
    """
    if isinstance(component, Container):
        target_package = component.publishable_entity.learning_package
    else:
        target_package = component.learning_package
    return PublishableEntityMapping.objects.get_or_create(
        source_usage_key=usage_key,
        target_entity=component.publishable_entity,
        target_package=target_package,
    )


def get_usage_key_string_from_staged_content(staged_content: 'StagedContent', block_id: str) -> str | None:
    """
    Get the usage ID from a staged content by block ID.
    """
    if staged_content.tags is None:
        return None
    return next((block_usage_id for block_usage_id in staged_content.tags if block_usage_id.endswith(block_id)), None)


def get_node_for_usage_key(node: etree._Element, usage_key: UsageKey) -> etree._Element:
    """
    Get the node in an XML tree which matches to the usage key.
    """
    if node.tag == usage_key.block_type and node.get('url_name') == usage_key.block_id:
        return node

    for child in node.getchildren():
        found = get_node_for_usage_key(child, usage_key)
        if found is not None:
            return found


def get_items_to_import(import_event: Import) -> list['XBlock']:
    """
    Collect items to import from a course.
    """
    items_to_import: list['XBlock'] = []
    if isinstance(import_event.source_key, CourseLocator):
        items_to_import.extend(
            modulestore().get_items(import_event.source_key, qualifiers={"category": "chapter"}) or []
        )
        items_to_import.extend(
            modulestore().get_items(import_event.source_key, qualifiers={"category": "static_tab"}) or []
        )

    return items_to_import


def cancel_incomplete_old_imports(import_event: Import) -> None:
    """
    Cancel any incomplete imports that have the same target as the current import.

    When a new import is created, we want to cancel any other incomplete user imports that have the same target.
    """
    incomplete_user_imports_with_same_target = Import.objects.filter(
        user=import_event.user,
        target_change=import_event.target_change,
        source_key=import_event.source_key,
        staged_content_for_import__isnull=False
    ).exclude(uuid=import_event.uuid)
    for incomplete_import in incomplete_user_imports_with_same_target:
        incomplete_import.set_status(ImportStatus.CANCELED)
