"""
Performance test for asset metadata in the modulestore.
"""
from path import Path as path
import unittest
from tempfile import mkdtemp
import itertools
from shutil import rmtree
from bson.code import Code
import datetime
import ddt
#from nose.plugins.attrib import attr

from nose.plugins.skip import SkipTest
from xmodule.assetstore import AssetMetadata
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.xml_importer import import_course_from_xml
from xmodule.modulestore.xml_exporter import export_course_to_xml
from xmodule.modulestore.tests.utils import (
    MODULESTORE_SETUPS,
    SHORT_NAME_MAP,
    TEST_DATA_DIR,
)
from xmodule.modulestore.perf_tests.generate_asset_xml import make_asset_xml, validate_xml, ASSET_XSD_FILE

# The dependency below needs to be installed manually from the development.txt file, which doesn't
# get installed during unit tests!
try:
    from code_block_timer import CodeBlockTimer
except ImportError:
    CodeBlockTimer = None

# Number of assets saved in the modulestore per test run.
ASSET_AMOUNT_PER_TEST = (0, 1, 10, 100, 1000, 10000)

# Use only this course in asset metadata performance testing.
COURSE_NAME = 'manual-testing-complete'

# A list of courses to test - only one.
TEST_COURSE = (COURSE_NAME, )

ALL_SORTS = (
    ('displayname', ModuleStoreEnum.SortOrder.ascending),
    ('displayname', ModuleStoreEnum.SortOrder.descending),
    ('uploadDate', ModuleStoreEnum.SortOrder.ascending),
    ('uploadDate', ModuleStoreEnum.SortOrder.descending),
)

# pylint: disable=invalid-name
TEST_DIR = path(__file__).dirname()
PLATFORM_ROOT = TEST_DIR.parent.parent.parent.parent.parent.parent
TEST_DATA_ROOT = PLATFORM_ROOT / TEST_DATA_DIR
COURSE_DATA_DIR = TEST_DATA_ROOT / COURSE_NAME

# Path where generated asset file is saved.
ASSET_XML_PATH = COURSE_DATA_DIR / AssetMetadata.EXPORTED_ASSET_DIR / AssetMetadata.EXPORTED_ASSET_FILENAME

# Path where asset XML schema definition file is located.
ASSET_XSD_PATH = PLATFORM_ROOT / "common" / "lib" / "xmodule" / "xmodule" / "assetstore" / "tests" / ASSET_XSD_FILE


@ddt.ddt
# Eventually, exclude this attribute from regular unittests while running *only* tests
# with this attribute during regular performance tests.
# @attr("perf_test")
@unittest.skip
class CrossStoreXMLRoundtrip(unittest.TestCase):
    """
    This class exists to time XML import and export between different modulestore
    classes with different amount of asset metadata.
    """

    # Use this attribute to skip this test on regular unittest CI runs.
    perf_test = True

    def setUp(self):
        super(CrossStoreXMLRoundtrip, self).setUp()
        self.export_dir = mkdtemp()
        self.addCleanup(rmtree, self.export_dir, ignore_errors=True)

    @ddt.data(*itertools.product(
        MODULESTORE_SETUPS,
        MODULESTORE_SETUPS,
        ASSET_AMOUNT_PER_TEST
    ))
    @ddt.unpack
    def test_generate_import_export_timings(self, source_ms, dest_ms, num_assets):
        """
        Generate timings for different amounts of asset metadata and different modulestores.
        """
        if CodeBlockTimer is None:
            raise SkipTest("CodeBlockTimer undefined.")

        desc = "XMLRoundTrip:{}->{}:{}".format(
            SHORT_NAME_MAP[source_ms],
            SHORT_NAME_MAP[dest_ms],
            num_assets
        )

        with CodeBlockTimer(desc):

            with CodeBlockTimer("fake_assets"):
                # First, make the fake asset metadata.
                make_asset_xml(num_assets, ASSET_XML_PATH)
                validate_xml(ASSET_XSD_PATH, ASSET_XML_PATH)

            with source_ms.build() as (source_content, source_store):
                with dest_ms.build() as (dest_content, dest_store):
                    source_course_key = source_store.make_course_key('a', 'course', 'course')
                    dest_course_key = dest_store.make_course_key('a', 'course', 'course')

                    with CodeBlockTimer("initial_import"):
                        import_course_from_xml(
                            source_store,
                            'test_user',
                            TEST_DATA_ROOT,
                            source_dirs=TEST_COURSE,
                            static_content_store=source_content,
                            target_id=source_course_key,
                            create_if_not_present=True,
                            raise_on_failure=True,
                        )

                    with CodeBlockTimer("export"):
                        export_course_to_xml(
                            source_store,
                            source_content,
                            source_course_key,
                            self.export_dir,
                            'exported_source_course',
                        )

                    with CodeBlockTimer("second_import"):
                        import_course_from_xml(
                            dest_store,
                            'test_user',
                            self.export_dir,
                            source_dirs=['exported_source_course'],
                            static_content_store=dest_content,
                            target_id=dest_course_key,
                            create_if_not_present=True,
                            raise_on_failure=True,
                        )


@ddt.ddt
# Eventually, exclude this attribute from regular unittests while running *only* tests
# with this attribute during regular performance tests.
# @attr("perf_test")
@unittest.skip
class FindAssetTest(unittest.TestCase):
    """
    This class exists to time asset finding in different modulestore
    classes with different amounts of asset metadata.
    """

    # Use this attr to skip this test on regular unittest CI runs.
    perf_test = True

    def setUp(self):
        super(FindAssetTest, self).setUp()
        self.export_dir = mkdtemp()
        self.addCleanup(rmtree, self.export_dir, ignore_errors=True)

    @ddt.data(*itertools.product(
        MODULESTORE_SETUPS,
        ASSET_AMOUNT_PER_TEST,
    ))
    @ddt.unpack
    def test_generate_find_timings(self, source_ms, num_assets):
        """
        Generate timings for different amounts of asset metadata and different modulestores.
        """
        if CodeBlockTimer is None:
            raise SkipTest("CodeBlockTimer undefined.")

        desc = "FindAssetTest:{}:{}".format(
            SHORT_NAME_MAP[source_ms],
            num_assets,
        )

        with CodeBlockTimer(desc):

            with CodeBlockTimer("fake_assets"):
                # First, make the fake asset metadata.
                make_asset_xml(num_assets, ASSET_XML_PATH)
                validate_xml(ASSET_XSD_PATH, ASSET_XML_PATH)

            with source_ms.build() as (source_content, source_store):
                source_course_key = source_store.make_course_key('a', 'course', 'course')
                asset_key = source_course_key.make_asset_key(
                    AssetMetadata.GENERAL_ASSET_TYPE, 'silly_cat_picture.gif'
                )

                with CodeBlockTimer("initial_import"):
                    import_course_from_xml(
                        source_store,
                        'test_user',
                        TEST_DATA_ROOT,
                        source_dirs=TEST_COURSE,
                        static_content_store=source_content,
                        target_id=source_course_key,
                        create_if_not_present=True,
                        raise_on_failure=True,
                    )

                with CodeBlockTimer("find_nonexistent_asset"):
                    # More correct would be using the AssetManager.find() - but since the test
                    # has created its own test modulestore, the AssetManager can't be used.
                    __ = source_store.find_asset_metadata(asset_key)

                # Perform get_all_asset_metadata for each sort.
                for sort in ALL_SORTS:
                    with CodeBlockTimer("get_asset_list:{}-{}".format(
                        sort[0],
                        'asc' if sort[1] == ModuleStoreEnum.SortOrder.ascending else 'desc'
                    )):
                        # Grab two ranges of 50 assets using different sorts.
                        # Why 50? That's how many are displayed on the current Studio "Files & Uploads" page.
                        start_middle = num_assets / 2
                        __ = source_store.get_all_asset_metadata(
                            source_course_key, 'asset', start=0, sort=sort, maxresults=50
                        )
                        __ = source_store.get_all_asset_metadata(
                            source_course_key, 'asset', start=start_middle, sort=sort, maxresults=50
                        )


@ddt.ddt
# Eventually, exclude this attribute from regular unittests while running *only* tests
# with this attribute during regular performance tests.
# @attr("perf_test")
@unittest.skip
class TestModulestoreAssetSize(unittest.TestCase):
    """
    This class exists to measure the size of asset metadata in ifferent modulestore
    classes with different amount of asset metadata.
    """

    # Use this attribute to skip this test on regular unittest CI runs.
    perf_test = True

    test_run_time = datetime.datetime.now()

    @ddt.data(*itertools.product(
        MODULESTORE_SETUPS,
        ASSET_AMOUNT_PER_TEST
    ))
    @ddt.unpack
    def test_asset_sizes(self, source_ms, num_assets):
        """
        Generate timings for different amounts of asset metadata and different modulestores.
        """
        # First, make the fake asset metadata.
        make_asset_xml(num_assets, ASSET_XML_PATH)
        validate_xml(ASSET_XSD_PATH, ASSET_XML_PATH)

        with source_ms.build() as (source_content, source_store):
            source_course_key = source_store.make_course_key('a', 'course', 'course')

            import_course_from_xml(
                source_store,
                'test_user',
                TEST_DATA_ROOT,
                source_dirs=TEST_COURSE,
                static_content_store=source_content,
                target_id=source_course_key,
                create_if_not_present=True,
                raise_on_failure=True,
            )

            asset_collection = source_ms.asset_collection()
            # Ensure the asset collection exists.
            if asset_collection.name in asset_collection.database.collection_names():

                # Map gets the size of each structure.
                mapper = Code("""
                    function() { emit("size", (this == null) ? 0 : Object.bsonsize(this)) }
                    """)

                # Reduce finds the largest structure size and returns only it.
                reducer = Code("""
                    function(key, values) {
                        var max_size = 0;
                        for (var i=0; i < values.length; i++) {
                            if (values[i] > max_size) {
                                max_size = values[i];
                            }
                        }
                        return max_size;
                    }
                """)

                results = asset_collection.map_reduce(mapper, reducer, "size_results")
                result_str = "{} - Store: {:<15} - Num Assets: {:>6} - Result: {}\n".format(
                    self.test_run_time, SHORT_NAME_MAP[source_ms], num_assets, [r for r in results.find()]
                )
                with open("bson_sizes.txt", "a") as f:
                    f.write(result_str)
