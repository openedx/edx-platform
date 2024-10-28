"""
Implements ./manage.py cms migrate_legacy_library
"""
import logging

from django.contrib.auth.models import User   # pylint: disable=imported-auth-user
from django.core.management import BaseCommand

from opaque_keys.edx.locator import LibraryLocator, LibraryLocatorV2
from openedx.core.djangoapps.content_libraries.migration_api import migrate_legacy_library


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    @TODO
    """

    def add_arguments(self, parser):
        """
        Add arguments to the argument parser.
        """
        parser.add_argument(
            'legacy_library',
            type=LibraryLocator.from_string,
        )
        parser.add_argument(
            'new_library',
            type=LibraryLocatorV2.from_string,
        )
        parser.add_argument(
            'collection',
            type=str,
        )

    def handle(  # pylint: disable=arguments-differ
        self,
        legacy_library: LibraryLocator,
        new_library: LibraryLocatorV2,
        collection: str | None,
        **kwargs,
    ) -> None:
        """
        Handle the command.
        """
        user = User.objects.filter(is_superuser=True)[0]
        migrate_legacy_library(legacy_library, new_library, collection_slug=collection, user=user)
