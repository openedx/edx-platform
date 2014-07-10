"""
Tests for testing the modulestore settings migration code.
"""
import copy
from django.test import TestCase
from lms.envs.modulestore_settings import convert_module_store_setting_if_needed


class ModuleStoreSettingsMigration(TestCase):
    """
    Tests for the migration code for the module store settings
    """

    OLD_CONFIG = {
        "default": {
            "ENGINE": "xmodule.modulestore.xml.XMLModuleStore",
            "OPTIONS": {
                "data_dir": "directory",
                "default_class": "xmodule.hidden_module.HiddenDescriptor",
            },
            "DOC_STORE_CONFIG": {},
        }
    }

    OLD_CONFIG_WITH_DIRECT_MONGO = {
        "default": {
            "ENGINE": "xmodule.modulestore.mongo.MongoModuleStore",
            "OPTIONS": {
                "collection": "modulestore",
                "db": "edxapp",
                "default_class": "xmodule.hidden_module.HiddenDescriptor",
                "fs_root": "/edx/var/edxapp/data",
                "host": "localhost",
                "password": "password",
                "port": 27017,
                "render_template": "edxmako.shortcuts.render_to_string",
                "user": "edxapp"
            },
            "DOC_STORE_CONFIG": {},
        }
    }

    OLD_MIXED_CONFIG_WITH_DICT = {
        "default": {
            "ENGINE": "xmodule.modulestore.mixed.MixedModuleStore",
            "OPTIONS": {
                "mappings": {},
                "reference_type": "Location",
                "stores": {
                    "an_old_mongo_store": {
                        "DOC_STORE_CONFIG": {},
                        "ENGINE": "xmodule.modulestore.mongo.MongoModuleStore",
                        "OPTIONS": {
                            "collection": "modulestore",
                            "db": "test",
                            "default_class": "xmodule.hidden_module.HiddenDescriptor",
                        }
                    },
                    "default": {
                        "ENGINE": "the_default_store",
                        "OPTIONS": {
                            "option1": "value1",
                            "option2": "value2"
                        },
                        "DOC_STORE_CONFIG": {}
                    },
                    "xml": {
                        "ENGINE": "xmodule.modulestore.xml.XMLModuleStore",
                        "OPTIONS": {
                            "data_dir": "directory",
                            "default_class": "xmodule.hidden_module.HiddenDescriptor"
                        },
                        "DOC_STORE_CONFIG": {}
                    }
                }
            }
        }
    }

    def _get_mixed_stores(self, mixed_setting):
        """
        Helper for accessing stores in a configuration setting for the Mixed modulestore
        """
        return mixed_setting["default"]["OPTIONS"]["stores"]

    def assertStoreValuesEqual(self, store_setting1, store_setting2):
        """
        Tests whether the fields in the given store_settings are equal
        """
        store_fields = ["OPTIONS", "DOC_STORE_CONFIG"]
        for field in store_fields:
            self.assertEqual(store_setting1[field], store_setting2[field])

    def assertMigrated(self, old_setting):
        """
        Migrates the given setting and checks whether it correctly converted
        to an ordered list of stores within Mixed.
        """
        # pass a copy of the old setting since the migration modifies the given setting
        new_mixed_setting = convert_module_store_setting_if_needed(copy.deepcopy(old_setting))

        # check whether the configuration is encapsulated within Mixed.
        self.assertEqual(new_mixed_setting["default"]["ENGINE"], "xmodule.modulestore.mixed.MixedModuleStore")

        # check whether the stores are in an ordered list
        new_stores = self._get_mixed_stores(new_mixed_setting)
        self.assertIsInstance(new_stores, list)

        return new_mixed_setting, new_stores[0]

    def test_convert_into_mixed(self):
        old_setting = self.OLD_CONFIG
        _, new_default_store_setting = self.assertMigrated(old_setting)
        self.assertStoreValuesEqual(new_default_store_setting, old_setting["default"])
        self.assertEqual(new_default_store_setting["ENGINE"], old_setting["default"]["ENGINE"])

    def test_convert_from_old_mongo_to_draft_store(self):
        old_setting = self.OLD_CONFIG_WITH_DIRECT_MONGO
        _, new_default_store_setting = self.assertMigrated(old_setting)
        self.assertStoreValuesEqual(new_default_store_setting, old_setting["default"])
        self.assertEqual(new_default_store_setting["ENGINE"], "xmodule.modulestore.mongo.draft.DraftModuleStore")

    def test_convert_from_dict_to_list(self):
        old_mixed_setting = self.OLD_MIXED_CONFIG_WITH_DICT
        new_mixed_setting, new_default_store_setting = self.assertMigrated(old_mixed_setting)
        self.assertEqual(new_default_store_setting["ENGINE"], "the_default_store")

        # compare each store configured in mixed
        old_stores = self._get_mixed_stores(self.OLD_MIXED_CONFIG_WITH_DICT)
        new_stores = self._get_mixed_stores(new_mixed_setting)
        self.assertEqual(len(new_stores), len(old_stores))
        for new_store_setting in self._get_mixed_stores(new_mixed_setting):
            self.assertStoreValuesEqual(new_store_setting, old_stores[new_store_setting['NAME']])
