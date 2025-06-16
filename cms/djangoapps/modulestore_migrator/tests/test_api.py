"""
Test cases for the modulestore migrator API.
"""

import pytest
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.modulestore_migrator import api
from cms.djangoapps.modulestore_migrator.data import CompositionLevel
from cms.djangoapps.modulestore_migrator.models import ModulestoreMigration
from cms.djangoapps.modulestore_migrator.tests.factories import ContentLibraryFactory, ModulestoreSourceFactory


@pytest.mark.django_db
class TestModulestoreMigratorAPI(ModuleStoreTestCase):
    """
    Test cases for the modulestore migrator API.
    """

    def setUp(self):
        super().setUp()

        self.library = ContentLibraryFactory()

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
        assert modulestoremigration.composition_level == CompositionLevel.Component.value
        assert modulestoremigration.replace_existing is False
        assert modulestoremigration.task_status is not None
        assert modulestoremigration.task_status.user == user
