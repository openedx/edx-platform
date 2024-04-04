"""
Command to build or re-build the search index for courses (in Studio, i.e. Draft
mode), in Meilisearch.

See also cms/djangoapps/contentstore/management/commands/reindex_course.py which
indexes LMS (published) courses in ElasticSearch.
"""
import logging
import time

from django.conf import settings
from django.core.management import BaseCommand, CommandError

from openedx.core.djangoapps.content_libraries import api as lib_api
from openedx.core.djangoapps.content.search.documents import (
    Fields,
    searchable_doc_for_course_block,
    searchable_doc_for_library_block,
    STUDIO_INDEX_NAME,
)
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from .meili_mixin import MeiliCommandMixin


log = logging.getLogger(__name__)


class Command(MeiliCommandMixin, BaseCommand):
    """
    Build or re-build the search index for courses and libraries (in Studio, i.e. Draft mode)

    This is experimental and not recommended for production use.
    """

    def add_arguments(self, parser):
        parser.add_argument('--experimental', action='store_true')
        parser.set_defaults(experimental=False)

    def handle(self, *args, **options):
        """
        Build a new search index for Studio, containing content from courses and libraries
        """
        if not options["experimental"]:
            raise CommandError(
                "This command is experimental and not recommended for production. "
                "Use the --experimental argument to acknowledge and run it."
            )
        start_time = time.perf_counter()
        client = self.get_meilisearch_client()
        store = modulestore()

        # Get the lists of libraries
        self.stdout.write("Counting libraries...")
        lib_keys = [lib.library_key for lib in lib_api.ContentLibrary.objects.select_related('org').only('org', 'slug')]
        num_libraries = len(lib_keys)

        # Get the list of courses
        self.stdout.write("Counting courses...")
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            all_courses = store.get_courses()
        num_courses = len(all_courses)

        # Some counters so we can track our progress as indexing progresses:
        num_contexts = num_courses + num_libraries
        num_contexts_done = 0  # How many courses/libraries we've indexed
        num_blocks_done = 0  # How many individual components/XBlocks we've indexed

        self.stdout.write(f"Found {num_courses} courses and {num_libraries} libraries.")
        index_name = settings.MEILISEARCH_INDEX_PREFIX + STUDIO_INDEX_NAME
        with self.using_temp_index(index_name) as temp_index_name:
            ############## Configure the index ##############

            # The following index settings are best changed on an empty index.
            # Changing them on a populated index will "re-index all documents in the index, which can take some time"
            # and use more RAM. Instead, we configure an empty index then populate it one course/library at a time.

            # Mark usage_key as unique (it's not the primary key for the index, but nevertheless must be unique):
            client.index(temp_index_name).update_distinct_attribute(Fields.usage_key)
            # Mark which attributes can be used for filtering/faceted search:
            client.index(temp_index_name).update_filterable_attributes([
                Fields.block_type,
                Fields.context_key,
                Fields.org,
                Fields.tags,
                Fields.type,
                Fields.access_id,
            ])
            # Mark which attributes are used for keyword search, in order of importance:
            client.index(temp_index_name).update_searchable_attributes([
                Fields.display_name,
                Fields.block_id,
                Fields.content,
                Fields.tags,
                # Keyword search does _not_ search the course name, course ID, breadcrumbs, block type, or other fields.
            ])

            ############## Libraries ##############
            self.stdout.write("Indexing libraries...")
            for lib_key in lib_keys:
                self.stdout.write(f"{num_contexts_done + 1}/{num_contexts}. Now indexing library {lib_key}")
                docs = []
                for component in lib_api.get_library_components(lib_key):
                    metadata = lib_api.LibraryXBlockMetadata.from_component(lib_key, component)
                    doc = searchable_doc_for_library_block(metadata)
                    docs.append(doc)
                    num_blocks_done += 1
                if docs:
                    # Add all the docs in this library at once (usually faster than adding one at a time):
                    self.wait_for_meili_task(client.index(temp_index_name).add_documents(docs))
                self.wait_for_meili_task(client.index(temp_index_name).add_documents(docs))
                num_contexts_done += 1

            ############## Courses ##############
            self.stdout.write("Indexing courses...")
            for course in all_courses:
                self.stdout.write(
                    f"{num_contexts_done + 1}/{num_contexts}. Now indexing course {course.display_name} ({course.id})"
                )
                docs = []

                # Pre-fetch the course with all of its children:
                course = store.get_course(course.id, depth=None)

                def add_with_children(block):
                    """ Recursively index the given XBlock/component """
                    doc = searchable_doc_for_course_block(block)
                    docs.append(doc)  # pylint: disable=cell-var-from-loop
                    self.recurse_children(block, add_with_children)  # pylint: disable=cell-var-from-loop

                self.recurse_children(course, add_with_children)

                if docs:
                    # Add all the docs in this course at once (usually faster than adding one at a time):
                    self.wait_for_meili_task(client.index(temp_index_name).add_documents(docs))
                num_contexts_done += 1
                num_blocks_done += len(docs)

        elapsed_time = time.perf_counter() - start_time
        self.stdout.write(
            f"Done! {num_blocks_done} blocks indexed across {num_contexts_done} courses "
            f"and libraries in {elapsed_time:.0f}s."
        )

    def recurse_children(self, block, fn):
        """
        Recurse the children of an XBlock and call the given function for each

        The main purpose of this is just to wrap the loading of each child in
        try...except. Otherwise block.get_children() would do what we need.
        """
        if block.has_children:
            for child_id in block.children:
                try:
                    child = block.get_child(child_id)
                except Exception as err:  # pylint: disable=broad-except
                    log.exception(err)
                    self.stderr.write(f"Unable to load block {child_id}")
                else:
                    fn(child)
