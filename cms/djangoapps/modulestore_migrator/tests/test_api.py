"""
Test cases for the modulestore migrator API.
"""

from opaque_keys.edx.locator import LibraryLocatorV2
from openedx_learning.api import authoring as authoring_api
from organizations.tests.factories import OrganizationFactory
import pytest
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.modulestore_migrator import api
from cms.djangoapps.modulestore_migrator.data import CompositionLevel
from cms.djangoapps.modulestore_migrator.models import ModulestoreMigration
from cms.djangoapps.modulestore_migrator.tests.factories import ModulestoreSourceFactory
from openedx.core.djangoapps.content_libraries import api as lib_api


@pytest.mark.django_db
class TestModulestoreMigratorAPI(ModuleStoreTestCase):
    """
    Test cases for the modulestore migrator API.
    """

    def setUp(self):
        super().setUp()

        self.organization = OrganizationFactory()
        self.lib_key = LibraryLocatorV2.from_string(
            f"lib:{self.organization.short_name}:test-key"
        )
        lib_api.create_library(
            org=self.organization,
            slug=self.lib_key.slug,
            title="Test Library",
        )
        self.library = lib_api.ContentLibrary.objects.get(slug=self.lib_key.slug)
        self.learning_package = self.library.learning_package

    def test_start_migration_to_library(self):
        """
        Test that the API can start a migration to a library.
        """
        source = ModulestoreSourceFactory()
        user = UserFactory()

        api.start_migration_to_library(
            user=user,
            source_key=source.key,
            target_library_key=self.library.library_key,
            target_collection_slug=None,
            composition_level=CompositionLevel.Component.value,
            replace_existing=False,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.get()
        assert modulestoremigration.source.key == source.key
        assert (
            modulestoremigration.composition_level == CompositionLevel.Component.value
        )
        assert modulestoremigration.replace_existing is False
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
            target_library_key=self.library.library_key,
            target_collection_slug=collection_key,
            composition_level=CompositionLevel.Component.value,
            replace_existing=False,
            forward_source_to_target=False,
        )

        modulestoremigration = ModulestoreMigration.objects.get()
        assert modulestoremigration.target_collection.key == collection_key
