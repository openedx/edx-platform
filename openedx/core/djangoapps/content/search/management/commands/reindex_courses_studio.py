"""
Command to build or re-build the search index for courses (in Studio, i.e. Draft
mode), in Meilisearch.

See also cms/djangoapps/contentstore/management/commands/reindex_course.py which
indexes LMS (published) courses in ElasticSearch.
"""
import logging

from django.conf import settings
from django.core.management import BaseCommand

from openedx.core.djangoapps.content.search.documents import searchable_doc_for_course_block
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from .meili_mixin import MeiliCommandMixin


log = logging.getLogger(__name__)

STUDIO_COURSES_INDEX_NAME = "courseware_draft"


class Command(MeiliCommandMixin, BaseCommand):
    """
    Build or re-build the search index for courses (in Studio, i.e. Draft mode)
    """

    def handle(self, *args, **options):
        """
        Build a new search index
        """
        client = self.get_meilisearch_client()
        store = modulestore()

        # Get the list of libraries
        self.stdout.write("Counting courses...")
        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            all_courses = store.get_courses()
        num_courses = len(all_courses)
        self.stdout.write(f"Found {num_courses} courses.")

        index_name = settings.MEILISEARCH_INDEX_PREFIX + STUDIO_COURSES_INDEX_NAME
        with self.using_temp_index(index_name) as temp_index_name:
            self.stdout.write("Indexing documents...")
            num_courses_done = 0
            num_blocks_done = 0
            for course in all_courses:
                self.stdout.write(f"{num_courses_done}/{num_courses}. Now indexing {course.display_name} ({course.id})")
                docs = []

                def add_with_children(block):
                    """ Recursively index the given XBlock/component """
                    doc = searchable_doc_for_course_block(block)
                    docs.append(doc)  # pylint: disable=cell-var-from-loop
                    self.recurse_children(block, add_with_children)  # pylint: disable=cell-var-from-loop

                self.recurse_children(course, add_with_children)

                # Add all the docs in this library at once (usually faster than adding one at a time):
                self.wait_for_meili_task(client.index(temp_index_name).add_documents(docs))
                num_courses_done += 1
                num_blocks_done += len(docs)

        self.stdout.write(f"Done! {num_blocks_done} blocks indexed across {num_courses_done} courses.")

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
