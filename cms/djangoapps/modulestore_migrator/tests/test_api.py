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
        self.lib_key_v2_2 = LibraryLocatorV2.from_string(
            f"lib:{self.organization.short_name}:test-key-2"
        )
        lib_api.create_library(
            org=self.organization,
            slug=self.lib_key_v2.slug,
            title="Test Library",
        )
        lib_api.create_library(
            org=self.organization,
            slug=self.lib_key_v2_2.slug,
            title="Test Library 2",
        )
        self.library_v2 = lib_api.ContentLibrary.objects.get(slug=self.lib_key_v2.slug)
        self.library_v2_2 = lib_api.ContentLibrary.objects.get(slug=self.lib_key_v2_2.slug)
        self.learning_package = self.library_v2.learning_package
        self.learning_package_2 = self.library_v2_2.learning_package
        self.source_units = [
            BlockFactory.create(
                display_name=f"Unit {i}",
                category="vertical", parent_location=self.library.usage_key,
                user_id=self.user.id, publish_item=False,
            ) for i in [0, 1, 2]
        ]
        self.source_htmls = [
            BlockFactory.create(
                display_name=f"HTML {i}",
                category="html", parent_location=self.source_units[i].usage_key,
                user_id=self.user.id, publish_item=False,
            ) for i in [0, 1, 2]
        ]
        self.library = self.store.get_library(self.library.context_key)  # refresh children list

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

    def test_get_migrations_get_preferred_and_get_authoritative(self):
        """
        Test that the API can retrieve migration info.
        """
        user = UserFactory()

        source_key = self.lib_key
        target_key_1 = self.library_v2.library_key
        target_key_2 = self.library_v2_2.library_key
        target_key_fake = LibraryLocatorV2("fakeorg", "fakelib")
        authoring_api.create_collection(
            learning_package_id=self.learning_package.id,
            key="test-collection-1a",
            title="Test Collection A in Lib 1",
            created_by=user.id,
        )
        authoring_api.create_collection(
            learning_package_id=self.learning_package.id,
            key="test-collection-1b",
            title="Test Collection B in Lib 1",
            created_by=user.id,
        )
        authoring_api.create_collection(
            learning_package_id=self.learning_package_2.id,
            key="test-collection-2c",
            title="Test Collection C in Lib 2",
            created_by=user.id,
        )

        assert list(api.get_migrations(source_key)) == []
        assert api.get_preferred_migration(source_key) is None
        assert api.get_preferred_migration(source_key, target_key=target_key_1) is None
        assert api.get_preferred_migration(source_key, target_key=target_key_2) is None
        assert api.get_authoritative_migration(source_key=source_key) is None

        # Run two migrations.
        # The second one will use Fork as a the repeat_handling_strategy,
        # so we should end up with two copies of each source block.
        api.start_migration_to_library(
            user=user,
            source_key=source_key,
            target_library_key=target_key_1,
            target_collection_slug="test-collection-1a",
            composition_level=CompositionLevel.Unit.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )
        api.start_migration_to_library(
            user=user,
            source_key=source_key,
            target_library_key=target_key_1,
            target_collection_slug="test-collection-1b",
            composition_level=CompositionLevel.Unit.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Fork.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )
        api.start_migration_to_library(
            user=user,
            source_key=source_key,
            target_library_key=target_key_1,
            target_collection_slug="test-collection-1b",
            composition_level=CompositionLevel.Unit.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Update.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )
        api.start_migration_to_library(
            user=user,
            source_key=source_key,
            target_library_key=target_key_2,
            target_collection_slug="test-collection-2c",
            composition_level=CompositionLevel.Unit.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=False,
        )
        migration_1a_i, migration_1b_i, migration_1b_ii, migration_2c_i = api.get_migrations(source_key)
        assert migration_1a_i.is_successful
        assert migration_1b_i.is_successful
        assert migration_1b_ii.is_successful
        assert migration_2c_i.is_successful
        assert migration_1a_i.target_key == target_key_1
        assert migration_1a_i.target_title == "Test Library"
        assert migration_1a_i.target_collection_slug == "test-collection-1a"
        assert migration_1a_i.target_collection_title == "Test Collection A in Lib 1"
        assert migration_2c_i.target_title == "Test Library 2"
        assert migration_2c_i.target_key == target_key_2
        assert migration_2c_i.target_collection_slug == "test-collection-2c"
        assert migration_2c_i.target_collection_title == "Test Collection C in Lib 2"
        assert api.get_preferred_migration(source_key).pk == migration_1a_i.pk
        assert api.get_preferred_migration(source_key, target_key=target_key_1).pk == migration_1a_i.pk
        assert api.get_preferred_migration(source_key, target_key=target_key_2).pk == migration_2c_i.pk
        assert api.get_preferred_migration(source_key, target_key=target_key_fake) is None
        mappings_1a_i = migration_1a_i.load_block_mappings()
        mappings_1b_i = migration_1b_i.load_block_mappings()
        mappings_1b_ii = migration_1b_ii.load_block_mappings()
        mappings_2c_i = migration_2c_i.load_block_mappings()
        all_source_usage_keys = {
            self.source_htmls[0].usage_key, self.source_htmls[1].usage_key, self.source_htmls[2].usage_key,
            self.source_units[0].usage_key, self.source_units[1].usage_key, self.source_units[2].usage_key,
        }
        assert set(mappings_1a_i.keys()) == all_source_usage_keys
        assert set(mappings_1b_i.keys()) == all_source_usage_keys
        assert set(mappings_1b_ii.keys()) == all_source_usage_keys
        assert set(mappings_2c_i.keys()) == all_source_usage_keys
        assert not (set(mappings_1a_i.values()) & set(mappings_1b_i.values()))
        assert mappings_1a_i == mappings_1b_ii
        # Since forward_source_to_target=False,
        # we have had no authoritative migration yet.
        assert api.get_authoritative_migration(source_key) is None
        assert api.get_authoritative_block_migration(self.source_htmls[1]) is None
        assert api.get_authoritative_block_migration(self.source_units[1]) is None

        api.start_migration_to_library(
            user=user,
            source_key=source_key,
            target_library_key=target_key_2,
            target_collection_slug="test-collection-2",
            composition_level=CompositionLevel.Unit.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Update.value,
            preserve_url_slugs=True,
            forward_source_to_target=True,
        )
        migration_1a_i_reloaded, _1b_i, _1b_ii, _2c_i, migration_2c_ii = api.get_migrations(source_key)
        assert migration_1a_i_reloaded.pk == migration_1a_i.pk
        assert migration_2c_ii.is_successful
        assert api.get_preferred_migration(source_key, target_key=target_key_1).pk == migration_1a_i.pk
        assert api.get_preferred_migration(source_key, target_key=target_key_2).pk == migration_2c_ii.pk
        assert api.get_preferred_migration(source_key).pk == migration_2c_ii.pk
        authoritative = api.get_authoritative_migration(source_key)
        assert authoritative.target_key == target_key_2
        assert authoritative.target_collection_slug == "test-collection-2c"
        assert authoritative.pk == migration_2c_ii.pk
        assert api.get_authoritative_block_migration(self.source_htmls[1]).target_key.context_key == target_key_2
        assert api.get_authoritative_block_migration(self.source_units[1]).target_key.context_key == target_key_2

        api.start_migration_to_library(
            user=user,
            source_key=source_key,
            target_library_key=target_key_1,
            target_collection_slug="test-collection-1a",
            composition_level=CompositionLevel.Unit.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Update.value,
            preserve_url_slugs=True,
            forward_source_to_target=True,
        )
        _1a_i, _1b_i, _1b_ii, _2c_i, _2c_ii, migration_1a_ii = api.get_migrations(source_key)
        assert migration_1a_ii.is_successful
        assert api.get_preferred_migration(source_key, target_key=target_key_1).pk == migration_1a_ii.pk
        assert api.get_preferred_migration(source_key, target_key=target_key_2).pk == migration_2c_i.pk
        assert api.get_preferred_migration(source_key).pk == migration_1a_ii.pk
        authoritative = api.get_authoritative_migration(source_key)
        assert authoritative.target_key == target_key_1
        assert authoritative.target_collection_slug == "test-collection-1a"
        assert authoritative.pk == migration_1a_ii
        assert api.get_authoritative_block_migration(self.source_htmls[1]).target_key.context_key == target_key_1
        assert api.get_authoritative_block_migration(self.source_units[1]).target_key.context_key == target_key_1

    def test_get_all_migrations_info(self):
        """
        Test that the API can retrieve all migrations info for source keys.
        """
        user = UserFactory()

        collection_key = "test-collection"
        collection_key_2 = "test-collection"
        authoring_api.create_collection(
            learning_package_id=self.learning_package.id,
            key=collection_key,
            title="Test Collection",
            created_by=user.id,
        )
        authoring_api.create_collection(
            learning_package_id=self.learning_package_2.id,
            key=collection_key_2,
            title="Test Collection 2",
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
        api.start_migration_to_library(
            user=user,
            source_key=self.lib_key,
            target_library_key=self.library_v2_2.library_key,
            target_collection_slug=collection_key_2,
            composition_level=CompositionLevel.Component.value,
            repeat_handling_strategy=RepeatHandlingStrategy.Skip.value,
            preserve_url_slugs=True,
            forward_source_to_target=True,
        )
        with self.assertNumQueries(1):
            result = api.get_all_migrations_info([self.lib_key])
            row = result.get(self.lib_key)
            assert row is not None
            assert row[0].get('migrations__target__key') == str(self.lib_key_v2)
            assert row[0].get('migrations__target__title') == "Test Library"
            assert row[0].get('migrations__target_collection__key') == collection_key
            assert row[0].get('migrations__target_collection__title') == "Test Collection"

            assert row[1].get('migrations__target__key') == str(self.lib_key_v2_2)
            assert row[1].get('migrations__target__title') == "Test Library 2"
            assert row[1].get('migrations__target_collection__key') == collection_key_2
            assert row[1].get('migrations__target_collection__title') == "Test Collection 2"

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
        for key in self.source_htmls:
            assert result.get(key) is not None
