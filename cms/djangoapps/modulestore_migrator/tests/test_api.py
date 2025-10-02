"""
Test cases for the modulestore migrator API.
"""

import pytest
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_learning.api import authoring as authoring_api
from organizations.tests.factories import OrganizationFactory

from cms.djangoapps.contentstore.tests.test_libraries import LibraryTestCase
from cms.djangoapps.modulestore_migrator import api
from cms.djangoapps.modulestore_migrator.data import CompositionLevel, RepeatHandlingStrategy
from cms.djangoapps.modulestore_migrator.models import ModulestoreMigration
from cms.djangoapps.modulestore_migrator.tests.factories import ModulestoreSourceFactory
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content_libraries import api as lib_api

from xmodule.modulestore.tests.factories import BlockFactory, LibraryFactory


@pytest.mark.django_db
class TestModulestoreMigratorAPI(LibraryTestCase):
    """
    Test cases for the modulestore migrator API.
    """

    def setUp(self):
        super().setUp()

        self.organization = OrganizationFactory()
        self.lib_key_v2 = LibraryLocatorV2.from_string(
            f"lib:{self.organization.short_name}:test-key"
        )
        lib_api.create_library(
            org=self.organization,
            slug=self.lib_key_v2.slug,
            title="Test Library",
        )
        self.library_v2 = lib_api.ContentLibrary.objects.get(slug=self.lib_key_v2.slug)
        self.learning_package = self.library_v2.learning_package
        self.blocks = []
        for _ in range(3):
            self.blocks.append(self._add_simple_content_block().usage_key)

    def test_start_migration_to_library(self):
        """
        Test that the API can start a migration to a library.
        """
        source = ModulestoreSourceFactory()
        user = UserFactory()

        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library_v2.library_key,
            target_collection_slug=None,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.get()
        assert modulestoremigration.source.key == source.key
        assert (
            modulestoremigration.composition_level == CompositionLevel.Component.value
        )
        assert modulestoremigration.repeat_handling_strategy == RepeatHandlingStrategy.Skip.value
        assert modulestoremigration.preserve_url_slugs is True
        assert modulestoremigration.task_status is not None
        assert modulestoremigration.task_status.user == user

    def test_start_bulk_migration_to_library(self):
        """
        Test that the API can start a bulk migration to a library.
        """
        source = ModulestoreSourceFactory()
        source_2 = ModulestoreSourceFactory()
        user = UserFactory()

        api.start_bulk_migration_to_library(
            user=user,
            source_key_list=[source.key, source_2.key],
            target_library_key=self.library_v2.library_key,
            target_collection_slug_list=None,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.get(source=source)
        assert modulestoremigration.source.key == source.key
        assert (
            modulestoremigration.composition_level == CompositionLevel.Component.value
        )
        assert modulestoremigration.repeat_handling_strategy == RepeatHandlingStrategy.Skip.value
        assert modulestoremigration.preserve_url_slugs is True
        assert modulestoremigration.task_status is not None
        assert modulestoremigration.task_status.user == user

        modulestoremigration_2 = ModulestoreMigration.objects.get(source=source_2)
        assert modulestoremigration_2.source.key == source_2.key
        assert (
            modulestoremigration_2.composition_level == CompositionLevel.Component.value
        )
        assert modulestoremigration_2.repeat_handling_strategy == RepeatHandlingStrategy.Skip.value
        assert modulestoremigration_2.preserve_url_slugs is True
        assert modulestoremigration_2.task_status is not None
        assert modulestoremigration_2.task_status.user == user

    def test_start_migration_to_library_with_collection(self):
        """
        Test that the API can start a migration to a library with a target collection.
        """

        source = ModulestoreSourceFactory()
        user = UserFactory()

        collection_key = "test-collection"
        authoring_api.create_collection(
            learning_package_id=self.learning_package.id,
            key=collection_key,
            title="Test Collection",
            created_by=user.id,
        )

        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library_v2.library_key,
            target_collection_slug=collection_key,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.get()
        assert modulestoremigration.target_collection.key == collection_key

    def test_start_migration_to_library_with_strategy_skip(self):
        """
        Test that the API can start a migration to a library with a skip strategy.
        """
        library = LibraryFactory.create(modulestore=self.store)
        library_block = BlockFactory.create(
            parent=library,
            category="html",
            display_name="Original Block",
            publish_item=False,
        )
        source = ModulestoreSourceFactory(key=library.context_key)
        user = UserFactory()

        # Start a migration with the Skip strategy
        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library_v2.library_key,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.get()
        assert modulestoremigration.repeat_handling_strategy == RepeatHandlingStrategy.Skip.value

        migrated_components = lib_api.get_library_components(self.library_v2.library_key)
        assert len(migrated_components) == 1

        # Update the block, changing its name
        library_block.display_name = "Updated Block"
        self.store.update_item(library_block, user.id)

        # Migrate again using the Skip strategy
        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library_v2.library_key,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.last()
        assert modulestoremigration is not None
        assert modulestoremigration.repeat_handling_strategy == RepeatHandlingStrategy.Skip.value

        migrated_components_fork = lib_api.get_library_components(self.library_v2.library_key)
        assert len(migrated_components_fork) == 1

        component = lib_api.LibraryXBlockMetadata.from_component(
            self.library_v2.library_key, migrated_components_fork[0]
        )
        assert component.display_name == "Original Block"

    def test_start_migration_to_library_with_strategy_update(self):
        """
        Test that the API can start a migration to a library with a update strategy.
        """
        library = LibraryFactory.create(modulestore=self.store)
        library_block = BlockFactory.create(
            parent=library,
            category="html",
            display_name="Original Block",
            publish_item=False,
        )
        source = ModulestoreSourceFactory(key=library.context_key)
        user = UserFactory()

        # Start a migration with the Skip strategy
        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library_v2.library_key,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.get()
        assert modulestoremigration.repeat_handling_strategy == RepeatHandlingStrategy.Skip.value

        migrated_components = lib_api.get_library_components(self.library_v2.library_key)
        assert len(migrated_components) == 1

        # Update the block, changing its name
        library_block.display_name = "Updated Block"
        self.store.update_item(library_block, user.id)

        # Migrate again using the Skip strategy
        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library_v2.library_key,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Update.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.last()
        assert modulestoremigration is not None
        assert modulestoremigration.repeat_handling_strategy == RepeatHandlingStrategy.Update.value

        migrated_components_fork = lib_api.get_library_components(self.library_v2.library_key)
        assert len(migrated_components_fork) == 1

        component = lib_api.LibraryXBlockMetadata.from_component(
            self.library_v2.library_key, migrated_components_fork[0]
        )
        assert component.display_name == "Updated Block"

    def test_start_migration_to_library_with_strategy_forking(self):
        """
        Test that the API can start a migration to a library with a forking strategy.
        """
        library = LibraryFactory.create(modulestore=self.store)
        library_block = BlockFactory.create(
            parent=library,
            category="html",
            display_name="Original Block",
            publish_item=False,
        )
        source = ModulestoreSourceFactory(key=library.context_key)
        user = UserFactory()

        # Start a migration with the Skip strategy
        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library_v2.library_key,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.get()
        assert modulestoremigration.repeat_handling_strategy == RepeatHandlingStrategy.Skip.value

        migrated_components = lib_api.get_library_components(self.library_v2.library_key)
        assert len(migrated_components) == 1

        # Update the block, changing its name
        library_block.display_name = "Updated Block"
        self.store.update_item(library_block, user.id)

        # Migrate again using the Fork strategy
        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library_v2.library_key,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Fork.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.last()
        assert modulestoremigration is not None
        assert modulestoremigration.repeat_handling_strategy == RepeatHandlingStrategy.Fork.value

        migrated_components_fork = lib_api.get_library_components(self.library_v2.library_key)
        assert len(migrated_components_fork) == 2

        first_component = lib_api.LibraryXBlockMetadata.from_component(
            self.library_v2.library_key, migrated_components_fork[0]
        )
        assert first_component.display_name == "Original Block"

        second_component = lib_api.LibraryXBlockMetadata.from_component(
            self.library_v2.library_key, migrated_components_fork[1]
        )
        assert second_component.display_name == "Updated Block"

        # Update the block again, changing its name
        library_block.display_name = "Updated Block Again"
        self.store.update_item(library_block, user.id)

        # Migrate again using the Fork strategy
        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library_v2.library_key,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Fork.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.last()
        assert modulestoremigration is not None
        assert modulestoremigration.repeat_handling_strategy == RepeatHandlingStrategy.Fork.value

        migrated_components_fork = lib_api.get_library_components(self.library_v2.library_key)
        assert len(migrated_components_fork) == 3

        first_component = lib_api.LibraryXBlockMetadata.from_component(
            self.library_v2.library_key, migrated_components_fork[0]
        )
        assert first_component.display_name == "Original Block"

        second_component = lib_api.LibraryXBlockMetadata.from_component(
            self.library_v2.library_key, migrated_components_fork[1]
        )
        assert second_component.display_name == "Updated Block"

        third_component = lib_api.LibraryXBlockMetadata.from_component(
            self.library_v2.library_key, migrated_components_fork[2]
        )
        assert third_component.display_name == "Updated Block Again"

    def test_get_migration_info(self):
        """
        Test that the API can retrieve migration info.
        """
        user = UserFactory()

        collection_key = "test-collection"
        authoring_api.create_collection(
            learning_package_id=self.learning_package.id,
            key=collection_key,
            title="Test Collection",
            created_by=user.id,
        )

        api.start_migration_to_library(
            user=user,
            source_key=self.lib_key,
            target_library_key=self.library_v2.library_key,
            target_collection_slug=collection_key,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=True,
        )
        with self.assertNumQueries(1):
            result = api.get_migration_info([self.lib_key])
            row = result.get(self.lib_key)
            assert row is not None
            assert row.migrations__target__key == str(self.lib_key_v2)
            assert row.migrations__target__title == "Test Library"
            assert row.migrations__target_collection__key == collection_key
        assert row.migrations__target_collection__title == "Test Collection"

    def test_get_target_block_usage_keys(self):
        """
        Test that the API can get the list of target block usage keys for a given library.
        """
        user = UserFactory()

        api.start_migration_to_library(
            user=user,
            source_key=self.lib_key,
            target_library_key=self.library_v2.library_key,
            target_collection_slug=None,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=True,
        )
        with self.assertNumQueries(1):
            result = api.get_target_block_usage_keys(self.lib_key)
        for key in self.blocks:
            assert result.get(key) is not None
