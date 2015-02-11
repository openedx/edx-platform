"""
Tests to verify correct number of MongoDB calls during course import/export and traversal
when using the Split modulestore.
"""

from tempfile import mkdtemp
from shutil import rmtree
from unittest import TestCase

from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.tests.factories import check_mongo_calls
from xmodule.modulestore.tests.test_cross_modulestore_import_export import (
    MongoContentstoreBuilder, MixedModulestoreBuilder, VersioningModulestoreBuilder,
    TEST_DATA_DIR
)

MIXED_SPLIT_MODULESTORE_BUILDER = MixedModulestoreBuilder([('split', VersioningModulestoreBuilder())])


class CountMongoCallsXMLRoundtrip(TestCase):
    """
    This class exists to test XML import and export to/from Split.
    """

    def setUp(self):
        super(CountMongoCallsXMLRoundtrip, self).setUp()
        self.export_dir = mkdtemp()
        self.addCleanup(rmtree, self.export_dir, ignore_errors=True)

    def test_import_export(self):
        # Construct the contentstore for storing the first import
        with MongoContentstoreBuilder().build() as source_content:
            # Construct the modulestore for storing the first import (using the previously created contentstore)
            with MIXED_SPLIT_MODULESTORE_BUILDER.build(source_content) as source_store:
                # Construct the contentstore for storing the second import
                with MongoContentstoreBuilder().build() as dest_content:
                    # Construct the modulestore for storing the second import (using the second contentstore)
                    with MIXED_SPLIT_MODULESTORE_BUILDER.build(dest_content) as dest_store:
                        source_course_key = source_store.make_course_key('a', 'course', 'course')
                        dest_course_key = dest_store.make_course_key('a', 'course', 'course')

                        with check_mongo_calls(16, 190):
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

                        with check_mongo_calls(37):
                            export_to_xml(
                                source_store,
                                source_content,
                                source_course_key,
                                self.export_dir,
                                'exported_source_course',
                            )

                        with check_mongo_calls(16, 189):
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


class CountMongoCallsCourseTraversal(TestCase):
    """
    Tests the number of Mongo calls made when traversing a course tree from the top course root
    to the leaf nodes.
    """

    def test_number_mongo_calls(self):
        # Construct the contentstore for storing the course import
        with MongoContentstoreBuilder().build() as source_content:
            # Construct the modulestore for storing the course import (using the previously created contentstore)
            with MIXED_SPLIT_MODULESTORE_BUILDER.build(source_content) as source_store:

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
                # pylint: disable=bad-continuation
                for depth, num_calls in (
                    (None, 7),  # The way this traversal *should* be done.
                    (0, 145)    # The pathological case - do *not* query a course this way!
                ):
                    with check_mongo_calls(num_calls):
                        start_block = source_store.get_course(source_course_key, depth=depth)
                        stack = [start_block]
                        while stack:
                            curr_block = stack.pop()
                            if curr_block.has_children:
                                for block in reversed(curr_block.get_children()):
                                    stack.append(block)
