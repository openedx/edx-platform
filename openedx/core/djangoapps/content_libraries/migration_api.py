"""
@@TODO
"""
from __future__ import annotations

import logging
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.db import transaction
from opaque_keys.edx.locator import LibraryLocator, LibraryLocatorV2
from openedx_learning.api.authoring import add_to_collection, get_collection
from openedx_learning.api.authoring_models import PublishableEntity, Component
from openedx_tagging.core.tagging.api import tag_object
from openedx_tagging.core.tagging.models import Taxonomy
from organizations.models import Organization
from xblock.fields import Scope

from openedx.core.djangoapps.xblock.api import load_block
from openedx.core.djangoapps.content_libraries.api import create_library_block
from xmodule.util.keys import BlockKey
from xmodule.modulestore.django import modulestore

from .models import ContentLibrary, LegacyLibraryMigrationSource, LegacyLibraryMigration, LegacyLibraryBlockMigration


log = logging.getLogger(__name__)


def migrate_legacy_library(
    source_key: LibraryLocator,
    target_key: LibraryLocatorV2,
    *,
    collection_slug: str | None,
    user: User,
    tags_to_add: dict[Taxonomy, list[str]] | None = None,
) -> None:
    """
    Migrate a v1 (legacy) library into a v2 (learning core) library, optionally within a collection.

    Use a single transaction so that if any step fails, nothing happens.

    @@TODO handle or document various exceptions
    """
    source = modulestore().get_library(source_key)
    target = ContentLibrary.objects.get(org=Organization.objects.get(short_name=target_key.org), slug=target_key.slug)
    assert target.learning_package_id
    collection = get_collection(target.learning_package_id, collection_slug) if collection_slug else None

    # We need to be careful not to conflict with any existing block keys in the target library.
    # This is unlikely to happen, since legacy library block ids are genreally randomly-generated GUIDs.
    # Howevever, there are a couple scenarios where it could arise:
    #  * An instance has two legacy libraries which were imported from the same source legacy library (and thus share
    #    block GUIDs) which the author now wants to merge together into one big new library.
    #  * A library was imported from handcrafted OLX, and thus has human-readable block IDs which are liable to overlap.
    # When there is conflict, we'll append "-1" to the end of the id (or "-2", "-3", etc., until we find a free ID).
    all_target_block_keys: set[BlockKey] = {
        BlockKey(*block_type_and_id)
        for block_type_and_id
        in Component.objects.filter(
            learning_package=target.learning_package,
            component_type__namespace="xblock.v1",
        ).values_list("component_type__name", "local_key")
    }

    # We also need to be careful not to conflict with other block IDs which we are moving in from the *source* library
    # This is very unlikely, but it could happen if, for example:
    # * the source library has a problem "foo", and
    # * the target library also has a problem "foo", and
    # * the source library ALSO has a problem "foo-1", thus
    # * the source library's "foo" must be moved to the target as "foo-2".
    all_source_block_keys: set[BlockKey] = {
        BlockKey.from_usage_key(child_key)
        for child_key in source.children
    }

    target_block_entity_keys: set[str] = set()

    with transaction.atomic():
        migration_source = LegacyLibraryMigrationSource.objects.get_or_create(source_key=source_key)
        migration = LegacyLibraryMigration(
            source=migration_source,
            target_library=target,
            target_collection=collection,
            migrated_by=user,
        )
        authoritative = "@@TODO"
        if authoritative:
            if migration_source.authoritative_migration:
                raise Exception("@@TODO")
            migration_source.authoritative_migration = migration
        migration.save()
        migration_source.save()

        for source_block in source.get_children():
            block_type: str = source_block.usage_key.block_type

            # Determine an available block_id...
            target_block_key = BlockKey(block_type, source_block.usage_key.block_id)
            if target_block_key in all_target_block_keys:
                suffix = 0
                while target_block_key in all_target_block_keys | all_source_block_keys:
                    suffix += 1
                    target_block_key = BlockKey(block_type, f"{source_block.usage_key.block_id}-{suffix}")

            # Create the block in the v2 library
            target_block_meta = create_library_block(
                library_key=target_key,
                block_type=block_type,
                definition_id=target_block_key.id,
                user_id=user.id,
            )
            target_block_entity_keys.add(f"xblock.v1:{block_type}:{target_block_key.id}")

            # Copy its content over from the v1 library
            target_block = load_block(target_block_meta.usage_key, user)
            for field_name, field in source_block.__class__.fields.items():
                if field.scope not in [Scope.settings, Scope.content]:
                    continue
                if not hasattr(target_block, field_name):
                    continue
                source_value = getattr(source_block, field_name)
                if getattr(target_block, field_name) != source_value:
                    setattr(target_block, field_name, source_value)
            target_block.save()

            # If requested, add tags
            for taxonomy, taxonomy_tags in (tags_to_add or {}).items():
                tag_object(str(target_block_meta.usage_key), taxonomy, taxonomy_tags)

            # Make a record of the migration
            LegacyLibraryBlockMigration.objects.create(
                library_migration=migration,
                block_type=block_type,
                source_block_id=source_block.usage_key.block_id,
                target_block_id=target_block_key.id,
            )

        # If requested, add to a collection, and add tags
        if collection_slug:
            add_to_collection(
                target.learning_package_id,
                collection_slug,
                PublishableEntity.objects.filter(
                    key__in=target_block_entity_keys,
                ),
            )
