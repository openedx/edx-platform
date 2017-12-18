"""
This config file extends the test environment configuration
so that we can run the lettuce acceptance tests.
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

import os

os.environ['EDXAPP_TEST_MONGO_HOST'] = os.environ.get('EDXAPP_TEST_MONGO_HOST', 'edx.devstack.mongo')

# noinspection PyUnresolvedReferences
from .acceptance import *

update_module_store_settings(
    MODULESTORE,
    doc_store_settings={
        'db': 'acceptance_xmodule',
        'host': MONGO_HOST,
        'port': MONGO_PORT_NUM,
        'collection': 'acceptance_modulestore_%s' % seed(),
    },
    module_store_options={
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': TEST_ROOT / "data",
    },
    default_store=os.environ.get('DEFAULT_STORE', 'draft'),
)

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': MONGO_HOST,
        'port': MONGO_PORT_NUM,
        'db': 'acceptance_xcontent_%s' % seed(),
    },
    # allow for additional options that can be keyed on a name, e.g. 'trashcan'
    'ADDITIONAL_OPTIONS': {
        'trashcan': {
            'bucket': 'trash_fs'
        }
    }
}

# Where to run: local, saucelabs, or grid
LETTUCE_SELENIUM_CLIENT = os.environ.get('LETTUCE_SELENIUM_CLIENT', 'grid')
SELENIUM_HOST = 'edx.devstack.{}'.format(LETTUCE_BROWSER)
SELENIUM_PORT = os.environ.get('SELENIUM_PORT', '4444')

SELENIUM_GRID = {
    'URL': 'http://{}:{}/wd/hub'.format(SELENIUM_HOST, SELENIUM_PORT),
    'BROWSER': LETTUCE_BROWSER,
}

# Point the URL used to test YouTube availability to our stub YouTube server
LETTUCE_HOST = os.environ['BOK_CHOY_HOSTNAME']
YOUTUBE['API'] = "http://{}:{}/get_youtube_api/".format(LETTUCE_HOST, YOUTUBE_PORT)
YOUTUBE['METADATA_URL'] = "http://{}:{}/test_youtube/".format(LETTUCE_HOST, YOUTUBE_PORT)
YOUTUBE['TEXT_API']['url'] = "{}:{}/test_transcripts_youtube/".format(LETTUCE_HOST, YOUTUBE_PORT)
