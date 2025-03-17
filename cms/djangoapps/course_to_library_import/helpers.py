"""
Helper functions for importing course content into a library.
"""

import logging
import mimetypes
from datetime import datetime, timezone

from django.db import transaction
from django.db.utils import IntegrityError
from lxml import etree

from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_learning.api import authoring as authoring_api

from openedx.core.djangoapps.content_libraries import api
from openedx.core.djangoapps.content_libraries.api import ContentLibrary
from openedx.core.djangoapps.content_staging import api as content_staging_api

from .data import CourseToLibraryImportStatus
from .models import ComponentVersionImport, CourseToLibraryImport
import os


log = logging.getLogger(__name__)


def create_block_in_library(block_to_import, usage_key, library_key, user_id, staged_content_id, override):
    """
    Create a block in a library from a staged content block.
    """
    now = datetime.now(tz=timezone.utc)
    staged_content_files = content_staging_api.get_staged_content_static_files(staged_content_id)

    assert isinstance(library_key, LibraryLocatorV2)
    content_library = ContentLibrary.objects.get_by_key(library_key)

    with transaction.atomic():
        component_type = authoring_api.get_or_create_component_type("xblock.v1", usage_key.block_type)
        component_version = None
        does_component_exist = authoring_api.get_components(
            content_library.learning_package.id
        ).filter(local_key=usage_key.block_id).exists()

        if does_component_exist:
            if not override:
                log.info(f"Component {usage_key.block_id} already exists in library {library_key}, skipping.")
                return
            else:
                component_version = _handle_component_override(
                    content_library, usage_key, etree.tostring(block_to_import)
                )

        if not override:
            # Create component (regardless of override path)
            _, library_usage_key = api.validate_can_add_block_to_library(
                library_key,
                block_to_import.tag,
                usage_key.block_id,
            )
            authoring_api.create_component(
                content_library.learning_package.id,
                component_type=component_type,
                local_key=usage_key.block_id,
                created=now,
                created_by=user_id,
            )

            component_version = api.set_library_block_olx(library_usage_key, etree.tostring(block_to_import))

        # Handle component version import records for overrides
        overrided_component_version_import = False
        if override:
            _update_component_version_import(
                component_version, usage_key, library_key, user_id
            )
            overrided_component_version_import = True

        _process_staged_content_files(
            component_version, staged_content_files, staged_content_id, usage_key,
            content_library, now, block_to_import, overrided_component_version_import, library_key, user_id
        )


def _handle_component_override(content_library, usage_key, new_content):
    """
    Create new ComponentVersion for overridden component.
    """
    component_version = None
    component = content_library.learning_package.component_set.filter(local_key=usage_key.block_id).first()

    if component:
        lib_usage_key = LibraryUsageLocatorV2(  # type: ignore[abstract]
            lib_key=content_library.library_key,
            block_type=component.component_type.name,
            usage_id=component.local_key,
        )
        component_version = api.set_library_block_olx(lib_usage_key, new_content)

    return component_version


def _update_component_version_import(component_version, usage_key, library_key, user_id):
    """
    Update component version import records for overridden components.
    """
    return ComponentVersionImport.objects.create(
        component_version=component_version,
        source_usage_key=usage_key,
        library_import=CourseToLibraryImport.objects.get(
            library_key=library_key,
            user_id=user_id,
            status=CourseToLibraryImportStatus.READY
        ),
    )


def _process_staged_content_files(
    component_version,
    staged_content_files,
    staged_content_id,
    usage_key,
    content_library,
    now,
    block_to_import,
    overrided_component_version_import,
    library_key,
    user_id,
):
    """
    Process staged content files for a component.
    """
    block_olx = etree.tostring(block_to_import).decode('utf-8')

    for staged_content_file_data in staged_content_files:
        original_filename = staged_content_file_data.filename
        file_basename = os.path.basename(original_filename)

        # Skip files not referenced in the block
        if file_basename not in block_olx:
            log.info(f"Skipping file {original_filename} as it is not referenced in block {usage_key}")
            continue

        file_data = content_staging_api.get_staged_content_static_file_data(
            staged_content_id,
            original_filename,
        )
        if not file_data:
            log.error(
                f"Staged content {staged_content_id} included referenced "
                f"file {original_filename}, but no file data was found."
            )
            continue

        filename = f"static/{str(usage_key)}"
        media_type_str, _ = mimetypes.guess_type(filename)
        if not media_type_str:
            media_type_str = "application/octet-stream"

        media_type = authoring_api.get_or_create_media_type(media_type_str)
        content = authoring_api.get_or_create_file_content(
            content_library.learning_package.id,
            media_type.id,
            data=file_data,
            created=now,
        )

        try:
            authoring_api.create_component_version_content(
                component_version.pk,
                content.id,
                key=filename,
            )
        except IntegrityError:
            pass  # Content already exists

        if not overrided_component_version_import:
            ComponentVersionImport.objects.get_or_create(
                component_version=component_version,
                source_usage_key=usage_key,
                library_import=CourseToLibraryImport.objects.get(
                    library_key=library_key,
                    user_id=user_id,
                    status=CourseToLibraryImportStatus.READY
                ),
            )


def flat_import_children(block_to_import, library_key, user_id, staged_content, override):
    """
    Import children of a block from staged content into a library.
    """
    staged_keys = [UsageKey.from_string(key) for key in staged_content.tags.keys()]
    block_id_to_usage_key = {key.block_id: key for key in staged_keys}

    for child in block_to_import.getchildren():
        if child.tag in ('chapter', 'sequential', 'vertical'):
            flat_import_children(child, library_key, user_id, staged_content, override)
        else:
            usage_key_str = child.get('url_name')

            if usage_key_str:
                usage_key = block_id_to_usage_key.get(usage_key_str)

                if usage_key and usage_key in staged_keys:
                    library = ContentLibrary.objects.filter(
                        org__short_name=library_key.org, slug=library_key.slug
                    ).first()
                    if not library:
                        raise ValueError(f"Library {library_key} does not exist.")
                    create_block_in_library(child, usage_key, library_key, user_id, staged_content.id, override)


def get_block_to_import(node, usage_key):
    """
    Get the block to import from a node.
    """
    if node.get('url_name') == usage_key.block_id:
        return node

    for child in node.getchildren():
        if found := get_block_to_import(child, usage_key):
            return found
