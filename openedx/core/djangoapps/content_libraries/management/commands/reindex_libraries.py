"""
Command to build or re-build the search index for content libraries.
"""
import logging
import time

from django.conf import settings
from django.core.management import BaseCommand, CommandError
import meilisearch
from meilisearch.errors import MeilisearchError
from meilisearch.models.task import TaskInfo

from openedx.core.djangoapps.content_libraries import api as lib_api
from openedx.core.djangoapps.content_libraries.search import searchable_doc_for_library_block
from openedx.core.djangoapps.content_libraries.models import ContentLibrary


log = logging.getLogger(__name__)

LIBRARIES_INDEX_NAME = "content_libraries"


class Command(BaseCommand):
    """
    Build or re-build the search index for content libraries.
    """

    def handle(self, *args, **options):
        """
        Build a new search index
        """

        # Connect to Meilisearch
        if not settings.MEILISEARCH_URL:
            raise CommandError("MEILISEARCH_URL is not set - search functionality disabled.")
        # TODO: put this into a helper lib?
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)
        try:
            client.health()
        except MeilisearchError as err:
            self.stderr.write(err.message)  # print this because 'raise...from...' doesn't print the details
            raise CommandError("Unable to connect to Meilisearch") from err

        # Get the list of libraries
        self.stdout.write("Counting libraries...")
        lib_keys = [lib.library_key for lib in ContentLibrary.objects.select_related('org').only('org', 'slug')]
        blocks_by_lib_key = {}
        num_blocks = 0
        for lib_key in lib_keys:
            blocks_by_lib_key[lib_key] = []
            for component in lib_api.get_library_components(lib_key):
                blocks_by_lib_key[lib_key].append(lib_api.LibraryXBlockMetadata.from_component(lib_key, component))
                num_blocks += 1

        self.stdout.write(f"Found {num_blocks} XBlocks among {len(lib_keys)} libraries.")

        # Check if the index exists already:
        self.stdout.write("Checking index...")
        index_name = settings.MEILISEARCH_INDEX_PREFIX + LIBRARIES_INDEX_NAME
        temp_index_name = index_name + "_new"
        try:
            client.get_index(temp_index_name)
        except MeilisearchError as err:
            pass
        else:
            self.stdout.write("Index already exists. Deleting it...")
            self._wait_for_meili_task(client, client.delete_index(temp_index_name))

        self.stdout.write("Creating new index...")
        self._wait_for_meili_task(
            client,
            client.create_index(temp_index_name, {'primaryKey': 'id'})
        )

        self.stdout.write("Indexing documents...")
        num_done = 0
        for lib_key in lib_keys:
            self.stdout.write(f"{num_done}/{num_blocks}. Now indexing {lib_key}")
            docs = []
            for metadata in blocks_by_lib_key[lib_key]:
                doc = searchable_doc_for_library_block(metadata)
                docs.append(doc)
            # Add all the docs in this library at once (usually faster than adding one at a time):
            self._wait_for_meili_task(client, client.index(temp_index_name).add_documents(docs))
            num_done += len(docs)

        new_index_created = client.get_index(temp_index_name).created_at
        if not self._index_exists(index_name, client):
            # We have to create the "target" index before we can successfully swap the new one into it:
            self.stdout.write(f"Preparing to swap into index (first time)...")
            self._wait_for_meili_task(client, client.create_index(index_name))
        self.stdout.write(f"Swapping index...")
        client.swap_indexes([{'indexes': [temp_index_name, index_name]}])
        # If we're using an API key that's restricted to certain index prefix(es), we won't be able to get the status
        # of this request unfortunately. https://github.com/meilisearch/meilisearch/issues/4103
        while True:
            time.sleep(1)
            if client.get_index(index_name).created_at != new_index_created:
                self.stdout.write("Waiting for swap completion...")
            else:
                break
        self.stdout.write("Deleting old index...")
        self._wait_for_meili_task(client, client.delete_index(temp_index_name))

        self.stdout.write(f"Done! {num_blocks} blocks indexed.")

    def _wait_for_meili_task(self, client: meilisearch.Client, info: TaskInfo):
        """
        Simple helper method to wait for a Meilisearch task to complete
        """
        current_status = client.get_task(info.task_uid)
        while current_status.status in ("enqueued", "processing"):
            self.stdout.write("...")
            time.sleep(1)
            current_status = client.get_task(info.task_uid)
        if current_status.status != "succeeded":
            self.stderr.write(f"Task has status: {current_status.status}")
            self.stderr.write(str(current_status.error))
            try:
                raise MeilisearchError(current_status.error['message'])
            except (TypeError, KeyError):
                raise MeilisearchError("Unknown error")

    def _index_exists(self, index_name: str, client: meilisearch.Client) -> bool:
        """
        Check if an index exists
        """
        try:
            client.get_index(index_name)
        except MeilisearchError as err:
            return False
        return True
