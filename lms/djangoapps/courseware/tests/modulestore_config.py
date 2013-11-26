"""
Define test configuration for modulestores.
"""

from xmodule.modulestore.tests.django_utils import xml_store_config, \
    mongo_store_config, draft_mongo_store_config,\
    mixed_store_config

from django.conf import settings

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)
TEST_DATA_MONGO_MODULESTORE = mongo_store_config(TEST_DATA_DIR)
TEST_DATA_DRAFT_MONGO_MODULESTORE = draft_mongo_store_config(TEST_DATA_DIR)

# Map all XML course fixtures so they are accessible through
# the MixedModuleStore
MAPPINGS = {
    'edX/simple/2012_Fall': 'xml',
    'edX/toy/2012_Fall': 'xml',
    'edX/toy/TT_2012_Fall': 'xml',
    'edX/test_end/2012_Fall': 'xml',
    'edX/test_about_blob_end_date/2012_Fall': 'xml',
    'edX/graded/2012_Fall': 'xml',
    'edX/open_ended/2012_Fall': 'xml',
    'edX/due_date/2013_fall': 'xml',
    'edX/open_ended_nopath/2012_Fall': 'xml',
}
TEST_DATA_MIXED_MODULESTORE = mixed_store_config(TEST_DATA_DIR, MAPPINGS)
