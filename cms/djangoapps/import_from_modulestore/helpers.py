"""
Helper functions for importing course content into a library.
"""
from datetime import datetime, timezone
import logging
import mimetypes
import os
import secrets

from django.db import transaction
from django.db.utils import IntegrityError
from lxml import etree

from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import CourseLocator, LibraryUsageLocatorV2
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import ContainerVersion

from openedx.core.djangoapps.content_libraries import api
from openedx.core.djangoapps.content_staging import api as content_staging_api
from xmodule.modulestore.django import modulestore

from .data import CompositionLevel
from .models import PublishableEntityMapping, PublishableEntityImport


log = logging.getLogger(__name__)
parser = etree.XMLParser(strip_cdata=False)


class ImportClient:
    """
    Client for importing course content into a library.

    This class handles the import of course content from staged content into a
    content library, creating the appropriate container hierarchy based on the
    specified composition level.
    """

    CONTAINER_CREATORS_MAP = {
        'chapter': authoring_api.create_unit_and_version,  # TODO: replace with create_module_and_version
        'sequential': authoring_api.create_unit_and_version,  # TODO: replace with create_section_and_version
        'vertical': authoring_api.create_unit_and_version,
    }

    CONTAINER_OVERRIDERS_MAP = {
        'chapter': authoring_api.create_next_unit_version,  # TODO: replace with create_next_module_version
        'sequential': authoring_api.create_next_unit_version,  # TODO: replace with create_next_section_version
        'vertical': authoring_api.create_next_unit_version,
    }

    def __init__(self, import_event, block_usage_id_to_import, staged_content, composition_level, override=False):
        self.import_event = import_event
        self.block_usage_id_to_import = block_usage_id_to_import
        self.staged_content = staged_content
        self.composition_level = composition_level
        self.override = override

        self.user_id = import_event.user_id
        self.content_library = import_event.target.contentlibrary
        self.library_key = self.content_library.library_key
        self.parser = etree.XMLParser(strip_cdata=False)

    def import_from_staged_content(self):
        """
        Import staged content into a library.
        """
        node = etree.fromstring(self.staged_content.olx, parser=parser)
        usage_key = UsageKey.from_string(self.block_usage_id_to_import)
        block_to_import = get_block_to_import(node, usage_key)
        if block_to_import is None:
            return

        self._process_import(self.block_usage_id_to_import, block_to_import)

    def get_or_create_container(self, container_type, key, display_name):
        """
        Create a container of the specified type.

        Creates a container (e.g., chapter, sequential, vertical) in the
        content library.
        """
        container_creator_func = self.CONTAINER_CREATORS_MAP.get(container_type)
        container_override_func = self.CONTAINER_OVERRIDERS_MAP.get(container_type)
        if not all((container_creator_func, container_override_func)):
            raise ValueError(f"Unknown container type: {container_type}")

        container_version = self.content_library.learning_package.publishable_entities.filter(key=key).first()
        if container_version and self.override:
            container_version = container_override_func(
                container_version.container,
                title=display_name or f"New {container_type}",
                components=[],
                created=datetime.now(tz=timezone.utc),
                created_by=self.import_event.user_id,
            )
        elif not container_version:
            _, container_version = container_creator_func(
                self.import_event.target_id,
                key=key or secrets.token_hex(16),
                title=display_name or f"New {container_type}",
                components=[],
                created=datetime.now(tz=timezone.utc),
                created_by=self.import_event.user_id,
            )

        return container_version

    def _process_import(self, usage_id, block_to_import):
        """
        Process import of a block from staged content into a library.

        Imports a block and its children into the library based on the
        composition level. It handles both simple and complicated blocks, creating
        the necessary container hierarchy.
        """
        usage_key = UsageKey.from_string(usage_id)
        result = []

        if block_to_import.tag not in CompositionLevel.COMPLICATED_LEVELS.value:
            return self._import_simple_block(block_to_import, usage_key)

        for child in block_to_import.getchildren():
            child_usage_id = get_usage_id_from_staged_content(self.staged_content, child.get('url_name'))
            if not child_usage_id:
                continue
            result.extend(self._import_child_block(child, child_usage_id))

        if self.composition_level in CompositionLevel.FLAT_LEVELS.value:
            return [component for component in result if not isinstance(component, ContainerVersion)]
        return result

    def _import_simple_block(self, block_to_import, usage_key) -> list:
        """
        Import a simple block into the library.

        Creates a block in the library from the staged content block.
        It returns a list containing the created component version.
        """
        component_version = self._create_block_in_library(block_to_import, usage_key)
        return [component_version] if component_version else []

    def _import_child_block(self, child, child_usage_id):
        """
        Import a child block into the library.

        Determines whether the child block is simple or complicated and
        delegates the import process to the appropriate helper method.
        """
        child_usage_key = UsageKey.from_string(child_usage_id)
        if child.tag in CompositionLevel.COMPLICATED_LEVELS.value:
            return self._import_complicated_child(child, child_usage_id)
        else:
            return self._import_simple_block(child, child_usage_key)

    def _import_complicated_child(self, child, child_usage_id):
        """
        Import a complicated child block into the library

        Handles the import of complicated child blocks, including creating
        containers and updating components.
        Returns a list containing the created container version.
        """
        if self.composition_level in CompositionLevel.FLAT_LEVELS.value:
            return self._process_import(child_usage_id, child)

        container_version = self.get_or_create_container(
            child.tag,
            child.get('url_name'),
            child.get('display_name', child.tag)
        )
        child_component_versions = self._process_import(child_usage_id, child)
        self._update_container_components(container_version, child_component_versions)
        return [container_version]

    def _update_container_components(self, container_version, component_versions):
        """
        Update components of a container.
        """
        return authoring_api.create_next_container_version(
            container_pk=container_version.container.pk,
            title=container_version.title,
            publishable_entities_pks=[
                cv.container.pk if isinstance(cv, ContainerVersion) else cv.component.pk for cv in component_versions
            ],
            entity_version_pks=[cv.pk for cv in component_versions],
            created=datetime.now(tz=timezone.utc),
            created_by=self.import_event.user_id,
            container_version_cls=container_version.__class__,
        )

    def _create_block_in_library(self, block_to_import, usage_key):
        """
        Create a block in a library from a staged content block.
        """
        now = datetime.now(tz=timezone.utc)
        staged_content_files = content_staging_api.get_staged_content_static_files(self.staged_content.id)

        with transaction.atomic():
            component_type = authoring_api.get_or_create_component_type("xblock.v1", usage_key.block_type)
            does_component_exist = authoring_api.get_components(
                self.import_event.target_id
            ).filter(local_key=usage_key.block_id).exists()

            if does_component_exist:
                if not self.override:
                    log.info(f"Component {usage_key.block_id} already exists in library {self.library_key}, skipping.")
                    return
                else:
                    component_version = self._handle_component_override(usage_key, etree.tostring(block_to_import))
            else:
                # Create component (regardless of override path)
                # FIXME check override logic
                _, library_usage_key = api.validate_can_add_block_to_library(
                    self.library_key,
                    block_to_import.tag,
                    usage_key.block_id,
                )
                authoring_api.create_component(
                    self.import_event.target_id,
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
            _create_publishable_entity_import(self.import_event, usage_key, component_version)

            return component_version

    def _handle_component_override(self, usage_key, new_content):
        """
        Create new ComponentVersion for overridden component.
        """
        component_version = None
        component = self.import_event.target.component_set.filter(local_key=usage_key.block_id).first()

        if component:
            library_usage_key = LibraryUsageLocatorV2(  # type: ignore[abstract]
                lib_key=self.library_key,
                block_type=component.component_type.name,
                usage_id=component.local_key,
            )
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
                self.import_event.target_id,
                media_type.id,
                data=file_data,
                created=created_at,
            )

            try:
                authoring_api.create_component_version_content(component_version.pk, content.id, key=filename)
            except IntegrityError:
                pass  # Content already exists


def _create_publishable_entity_import(import_event, usage_key, component_version) -> PublishableEntityImport:
    """
    Creates relations between the imported component and source usage key and import event.
    """
    publishable_entity_mapping, _ = _get_or_create_publishable_entity_mapping(
        usage_key,
        component_version.component
    )
    return PublishableEntityImport.objects.create(
        import_event=import_event,
        result=publishable_entity_mapping,
        resulting_draft=component_version.publishable_entity_version,
    )


def _get_or_create_publishable_entity_mapping(usage_key, component) -> tuple[PublishableEntityMapping, bool]:
    """
    Creates a mapping between the source usage key and the target publishable entity.
    """
    return PublishableEntityMapping.objects.get_or_create(
        source_usage_key=usage_key,
        target_entity=component.publishable_entity,
        target_package=component.learning_package
    )


def get_usage_id_from_staged_content(staged_content, block_id):
    """
    Get the usage ID from a staged content by block ID.
    """
    return next((block_usage_id for block_usage_id in staged_content.tags if block_usage_id.endswith(block_id)), None)


def get_block_to_import(node, usage_key):
    """
    Get the block to import from a node.
    """

    if node.get('url_name') == usage_key.block_id:
        return node

    for child in node.getchildren():
        found = get_block_to_import(child, usage_key)
        if found is not None:
            return found


def get_items_to_import(import_event):
    """
    Collect items to import from a course.
    """
    items_to_import = []
    if isinstance(import_event.source_key, CourseLocator):
        items_to_import.extend(
            modulestore().get_items(import_event.source_key, qualifiers={"category": "chapter"}) or []
        )
        items_to_import.extend(
            modulestore().get_items(import_event.source_key, qualifiers={"category": "static_tab"}) or []
        )

    return items_to_import
