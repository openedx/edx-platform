""" Management command to update content libraries' search index """


import logging

from textwrap import dedent

from django.core.management import BaseCommand
from opaque_keys.edx.locator import LibraryLocatorV2
from openedx.core.djangoapps.content_libraries.api import DRAFT_NAME
from openedx.core.djangoapps.content_libraries.libraries_index import ContentLibraryIndexer, LibraryBlockIndexer
from openedx.core.djangoapps.content_libraries.library_bundle import LibraryBundle
from openedx.core.djangoapps.content_libraries.models import ContentLibrary

from cms.djangoapps.contentstore.management.commands.prompt import query_yes_no


class Command(BaseCommand):
    """
    Command to reindex blockstore-based content libraries (single, multiple or all available).

    This isn't needed on a regular basis as signals in various library APIs update the index when creating, updating or
    deleting libraries.
    This is usually required when the schema of the index changes, or if indexes are out of sync due to indexing
    being previously disabled or any other reason.

    Examples:

        ./manage.py reindex_content_library lib1 lib2 - reindexes libraries with keys lib1 and lib2
        ./manage.py reindex_content_library --all - reindexes all available libraries
        ./manage.py reindex_content_library --clear-all - clear all libraries indexes
    """
    help = dedent(__doc__)
    CONFIRMATION_PROMPT_CLEAR = u"This will clear all indexed libraries from elasticsearch. Do you want to continue?"
    CONFIRMATION_PROMPT_ALL = u"Reindexing all libraries might be a time consuming operation. Do you want to continue?"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-all',
            action='store_true',
            dest='clear-all',
            help='Clear all library indexes'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            help='Reindex all libraries'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Run command without user prompt for confirmation'
        )
        parser.add_argument('library_ids', nargs='*')

    def handle(self, *args, **options):
        if options['clear-all']:
            if options['force'] or query_yes_no(self.CONFIRMATION_PROMPT_CLEAR, default="no"):
                self.clear_all()
            return

        if options['all']:
            if options['force'] or query_yes_no(self.CONFIRMATION_PROMPT_ALL, default="no"):
                logging.info("Indexing all libraries")
                library_ids = [str(library.library_key) for library in ContentLibrary.objects.all()]
                self.index_libraries(library_ids, True)
            else:
                return
        else:
            self.index_libraries(options['library_ids'])
            return

    def clear_all(self):
        """
        Remove all library and block indexes
        """
        logging.info("Removing all xblocks from the index")
        LibraryBlockIndexer.remove_all_items()
        logging.info("Removing all libraries from the index")
        ContentLibraryIndexer.remove_all_items()

    def index_libraries(self, library_ids, remove_stale_libraries=False):
        """
        Index the given libraries and their blocks
        """
        logging.info("Indexing libraries {}".format(', '.join(library_ids)))
        ContentLibraryIndexer.index_items(library_ids)

        for library_id in library_ids:
            library_key = LibraryLocatorV2.from_string(library_id)
            ref = ContentLibrary.objects.get_by_key(library_key)
            lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
            block_ids = {str(block) for block in lib_bundle.get_all_usages()}

            if block_ids:
                logging.info("Indexing library {}'s blocks: {}".format(library_id, ', '.join(block_ids)))
                LibraryBlockIndexer.index_items(block_ids)

            # Remove stale blocks from the library's index
            indexed_blocks = LibraryBlockIndexer.get_items(filter_terms={'library_key': [library_id]})
            indexed_block_ids = {block['id'] for block in indexed_blocks}
            blocks_to_unindex = indexed_block_ids.difference(block_ids)

            if blocks_to_unindex:
                logging.info("Unindex library {}'s deleted blocks: {}".format(library_id, ', '.join(blocks_to_unindex)))
                LibraryBlockIndexer.remove_items(blocks_to_unindex)

        if remove_stale_libraries:
            indexed_libraries = ContentLibraryIndexer.get_items(filter_terms={})
            indexed_library_ids = {library['id'] for library in indexed_libraries}
            libraries_to_unindex = indexed_library_ids.difference(library_ids)

            if libraries_to_unindex:
                logging.info("Unindex deleted libraries: {}".format(', '.join(libraries_to_unindex)))
                ContentLibraryIndexer.remove_items(libraries_to_unindex)

                for library_id in libraries_to_unindex:
                    # Remove all library's blocks from the index
                    indexed_blocks = LibraryBlockIndexer.get_items(filter_terms={'library_key': [library_id]})
                    if indexed_blocks:
                        logging.info("Unindex deleted library {}'s blocks: {}".format(library_id,
                                                                                      ','.join(libraries_to_unindex)))
                        LibraryBlockIndexer.remove_items([block['id'] for block in indexed_blocks])
