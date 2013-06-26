from uuid import uuid4

from django.conf import settings


def mongo_store_config(data_dir):
    """
    Defines default module store using MongoModuleStore.

    Use of this config requires mongo to be running.
    """
    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
            'OPTIONS': {
                'default_class': 'xmodule.raw_module.RawDescriptor',
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore',
                'fs_root': data_dir,
                'render_template': 'mitxmako.shortcuts.render_to_string'
            }
        }
    }
    store['direct'] = store['default']
    return store


def draft_mongo_store_config(data_dir):
    """
    Defines default module store using DraftMongoModuleStore.
    """

    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'host': 'localhost',
        'db': 'xmodule',
        'collection': 'modulestore_%s' % uuid4().hex,
        'fs_root': data_dir,
        'render_template': 'mitxmako.shortcuts.render_to_string'
    }

    return {
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
            'OPTIONS': modulestore_options
        },
        'direct': {
            'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
            'OPTIONS': modulestore_options
        }
    }


def xml_store_config(data_dir):
    """
    Defines default module store using XMLModuleStore.
    """
    return {
        'default': {
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        }
    }

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)
TEST_DATA_MONGO_MODULESTORE = mongo_store_config(TEST_DATA_DIR)
TEST_DATA_DRAFT_MONGO_MODULESTORE = draft_mongo_store_config(TEST_DATA_DIR)
