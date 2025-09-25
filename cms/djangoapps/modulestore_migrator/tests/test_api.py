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

    def test_forking_is_not_implemented(self):
        """
        Test that the API raises NotImplementedError for the Fork strategy.
        """
        source = ModulestoreSourceFactory()
        user = UserFactory()

        with pytest.raises(NotImplementedError):
            api.start_migration_to_library(
                user=user,
                source_key=source.key,
                target_library_key=self.library_v2.library_key,
                target_collection_slug=None,
                composition_level=CompositionLevel.Component.value,
                repeat_handling_strategy=RepeatHandlingStrategy.Fork.value,
                preserve_url_slugs=True,
                forward_source_to_target=False,
            )

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
