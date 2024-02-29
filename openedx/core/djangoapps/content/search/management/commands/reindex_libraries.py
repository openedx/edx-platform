"""
Command to build or re-build the search index for content libraries.
"""
import logging

from django.conf import settings
from django.core.management import BaseCommand

from openedx.core.djangoapps.content_libraries import api as lib_api
from openedx.core.djangoapps.content.search.documents import searchable_doc_for_library_block
from .meili_mixin import MeiliCommandMixin


log = logging.getLogger(__name__)

LIBRARIES_INDEX_NAME = "content_libraries"


class Command(MeiliCommandMixin, BaseCommand):
    """
    Build or re-build the search index for content libraries.
    """

    def handle(self, *args, **options):
        """
        Build a new search index
        """
        client = self.get_meilisearch_client()

        # Get the list of libraries
        self.stdout.write("Counting libraries...")
        lib_keys = [lib.library_key for lib in lib_api.ContentLibrary.objects.select_related('org').only('org', 'slug')]
        blocks_by_lib_key = {}
        num_blocks = 0
        for lib_key in lib_keys:
            blocks_by_lib_key[lib_key] = []
            for component in lib_api.get_library_components(lib_key):
                blocks_by_lib_key[lib_key].append(lib_api.LibraryXBlockMetadata.from_component(lib_key, component))
                num_blocks += 1

        self.stdout.write(f"Found {num_blocks} XBlocks among {len(lib_keys)} libraries.")

        index_name = settings.MEILISEARCH_INDEX_PREFIX + LIBRARIES_INDEX_NAME
        with self.using_temp_index(index_name) as temp_index_name:
            self.stdout.write("Indexing documents...")
            num_done = 0
            for lib_key in lib_keys:
                self.stdout.write(f"{num_done}/{num_blocks}. Now indexing {lib_key}")
                docs = []
                for metadata in blocks_by_lib_key[lib_key]:
                    doc = searchable_doc_for_library_block(metadata)
                    docs.append(doc)
                # Add all the docs in this library at once (usually faster than adding one at a time):
                self.wait_for_meili_task(client.index(temp_index_name).add_documents(docs))
                num_done += len(docs)

        self.stdout.write(f"Done! {num_done} blocks indexed.")
