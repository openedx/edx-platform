"""
Tests to verify correct number of MongoDB calls during course import/export and traversal
when using the Split modulestore.
"""

from tempfile import mkdtemp
from shutil import rmtree
from unittest import TestCase
import ddt

from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.tests.factories import check_mongo_calls
from xmodule.modulestore.tests.test_cross_modulestore_import_export import (
    MixedModulestoreBuilder, VersioningModulestoreBuilder,
    MongoModulestoreBuilder, TEST_DATA_DIR
)

MIXED_OLD_MONGO_MODULESTORE_BUILDER = MixedModulestoreBuilder([('draft', MongoModulestoreBuilder())])
MIXED_SPLIT_MODULESTORE_BUILDER = MixedModulestoreBuilder([('split', VersioningModulestoreBuilder())])


@ddt.ddt
class CountMongoCallsXMLRoundtrip(TestCase):
    """
    This class exists to test XML import and export to/from Split.
    """

    def setUp(self):
        super(CountMongoCallsXMLRoundtrip, self).setUp()
        self.export_dir = mkdtemp()
        self.addCleanup(rmtree, self.export_dir, ignore_errors=True)

    @ddt.data(
        (MIXED_OLD_MONGO_MODULESTORE_BUILDER, 287, 780, 702, 702),
        (MIXED_SPLIT_MODULESTORE_BUILDER, 37, 16, 190, 189),
    )
    @ddt.unpack
    def test_import_export(self, store_builder, export_reads, import_reads, first_import_writes, second_import_writes):
        with store_builder.build() as (source_content, source_store):
            with store_builder.build() as (dest_content, dest_store):
                source_course_key = source_store.make_course_key('a', 'course', 'course')
                dest_course_key = dest_store.make_course_key('a', 'course', 'course')

                # An extra import write occurs in the first Split import due to the mismatch between
                # the course id and the wiki_slug in the test XML course. The course must be updated
                # with the correct wiki_slug during import.
                with check_mongo_calls(import_reads, first_import_writes):
                    import_from_xml(
                        source_store,
                        'test_user',
                        TEST_DATA_DIR,
                        course_dirs=['manual-testing-complete'],
                        static_content_store=source_content,
                        target_course_id=source_course_key,
                        create_course_if_not_present=True,
                        raise_on_failure=True,
                    )

                with check_mongo_calls(export_reads):
                    export_to_xml(
                        source_store,
                        source_content,
                        source_course_key,
                        self.export_dir,
                        'exported_source_course',
                    )

                with check_mongo_calls(import_reads, second_import_writes):
                    import_from_xml(
                        dest_store,
                        'test_user',
                        self.export_dir,
                        course_dirs=['exported_source_course'],
                        static_content_store=dest_content,
                        target_course_id=dest_course_key,
                        create_course_if_not_present=True,
                        raise_on_failure=True,
                    )


@ddt.ddt
class CountMongoCallsCourseTraversal(TestCase):
    """
    Tests the number of Mongo calls made when traversing a course tree from the top course root
    to the leaf nodes.
    """

    @ddt.data(
        (MIXED_OLD_MONGO_MODULESTORE_BUILDER, None, 189),  # The way this traversal *should* be done.
        (MIXED_OLD_MONGO_MODULESTORE_BUILDER, 0, 387),     # The pathological case - do *not* query a course this way!
        (MIXED_SPLIT_MODULESTORE_BUILDER, None, 7),  # The way this traversal *should* be done.
        (MIXED_SPLIT_MODULESTORE_BUILDER, 0, 145)    # The pathological case - do *not* query a course this way!
    )
    @ddt.unpack
    def test_number_mongo_calls(self, store, depth, num_mongo_calls):
        with store.build() as (source_content, source_store):

            source_course_key = source_store.make_course_key('a', 'course', 'course')

            # First, import a course.
            import_from_xml(
                source_store,
                'test_user',
                TEST_DATA_DIR,
                course_dirs=['manual-testing-complete'],
                static_content_store=source_content,
                target_course_id=source_course_key,
                create_course_if_not_present=True,
                raise_on_failure=True,
            )

            # Course traversal modeled after the traversal done here:
            # lms/djangoapps/mobile_api/video_outlines/serializers.py:BlockOutline
            # Starting at the root course block, do a breadth-first traversal using
            # get_children() to retrieve each block's children.
            with check_mongo_calls(num_mongo_calls):
                start_block = source_store.get_course(source_course_key, depth=depth)
                stack = [start_block]
                while stack:
                    curr_block = stack.pop()
                    if curr_block.has_children:
                        for block in reversed(curr_block.get_children()):
                            stack.append(block)
