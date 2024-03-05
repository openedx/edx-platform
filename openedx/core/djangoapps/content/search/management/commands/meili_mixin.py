"""
Mixin for Django management commands that interact with Meilisearch
"""
from contextlib import contextmanager
import time

from django.conf import settings
from django.core.management import CommandError
import meilisearch
from meilisearch.errors import MeilisearchError
from meilisearch.models.task import TaskInfo


class MeiliCommandMixin:
    """
    Mixin for Django management commands that interact with Meilisearch
    """
    def get_meilisearch_client(self):
        """
        Get the Meiliesearch client
        """
        if hasattr(self, "_meili_client"):
            return self._meili_client
        # Connect to Meilisearch
        if not settings.MEILISEARCH_URL:
            raise CommandError("MEILISEARCH_URL is not set - search functionality disabled.")

        self._meili_client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)
        try:
            self._meili_client.health()
        except MeilisearchError as err:
            self.stderr.write(err.message)  # print this because 'raise...from...' doesn't print the details
            raise CommandError("Unable to connect to Meilisearch") from err
        return self._meili_client

    def wait_for_meili_task(self, info: TaskInfo):
        """
        Simple helper method to wait for a Meilisearch task to complete
        """
        client = self.get_meilisearch_client()
        current_status = client.get_task(info.task_uid)
        while current_status.status in ("enqueued", "processing"):
            self.stdout.write("...")
            time.sleep(1)
            current_status = client.get_task(info.task_uid)
        if current_status.status != "succeeded":
            self.stderr.write(f"Task has status: {current_status.status}")
            self.stderr.write(str(current_status.error))
            try:
                err_reason = current_status.error['message']
            except (TypeError, KeyError):
                err_reason = "Unknown error"
            raise MeilisearchError(err_reason)

    def index_exists(self, index_name: str) -> bool:
        """
        Check if an index exists
        """
        client = self.get_meilisearch_client()
        try:
            client.get_index(index_name)
        except MeilisearchError as err:
            if err.code == "index_not_found":
                return False
            else:
                raise err
        return True

    @contextmanager
    def using_temp_index(self, target_index):
        """
        Create a new temporary Meilisearch index, populate it, then swap it to
        become the active index.
        """
        client = self.get_meilisearch_client()
        self.stdout.write("Checking index...")
        temp_index_name = target_index + "_new"
        if self.index_exists(temp_index_name):
            self.stdout.write("Temporary index already exists. Deleting it...")
            self.wait_for_meili_task(client.delete_index(temp_index_name))

        self.stdout.write("Creating new index...")
        self.wait_for_meili_task(
            client.create_index(temp_index_name, {'primaryKey': 'id'})
        )
        new_index_created = client.get_index(temp_index_name).created_at

        yield temp_index_name

        if not self.index_exists(target_index):
            # We have to create the "target" index before we can successfully swap the new one into it:
            self.stdout.write("Preparing to swap into index (first time)...")
            self.wait_for_meili_task(client.create_index(target_index))
        self.stdout.write("Swapping index...")
        client.swap_indexes([{'indexes': [temp_index_name, target_index]}])
        # If we're using an API key that's restricted to certain index prefix(es), we won't be able to get the status
        # of this request unfortunately. https://github.com/meilisearch/meilisearch/issues/4103
        while True:
            time.sleep(1)
            if client.get_index(target_index).created_at != new_index_created:
                self.stdout.write("Waiting for swap completion...")
            else:
                break
        self.stdout.write("Deleting old index...")
        self.wait_for_meili_task(client.delete_index(temp_index_name))
