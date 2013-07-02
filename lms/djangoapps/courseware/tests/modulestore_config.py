from xmodule.modulestore.tests.django_utils import xml_store_config, mongo_store_config, draft_mongo_store_config

from django.conf import settings

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)
TEST_DATA_MONGO_MODULESTORE = mongo_store_config(TEST_DATA_DIR)
TEST_DATA_DRAFT_MONGO_MODULESTORE = draft_mongo_store_config(TEST_DATA_DIR)
