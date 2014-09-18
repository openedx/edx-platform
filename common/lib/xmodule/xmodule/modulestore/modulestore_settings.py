"""
This file contains helper functions for configuring module_store_setting settings and support for backward compatibility with older formats.
"""

import warnings
import copy


def convert_module_store_setting_if_needed(module_store_setting):
    """
    Converts old-style module_store_setting configuration settings to the new format.
    """

    def convert_old_stores_into_list(old_stores):
        """
        Converts and returns the given stores in old (unordered) dict-style format to the new (ordered) list format
        """
        new_store_list = []
        for store_name, store_settings in old_stores.iteritems():

            store_settings['NAME'] = store_name
            if store_name == 'default':
                new_store_list.insert(0, store_settings)
            else:
                new_store_list.append(store_settings)

            # migrate request for the old 'direct' Mongo store to the Draft store
            if store_settings['ENGINE'] == 'xmodule.modulestore.mongo.MongoModuleStore':
                warnings.warn("MongoModuleStore is deprecated! Please use DraftModuleStore.", DeprecationWarning)
                store_settings['ENGINE'] = 'xmodule.modulestore.mongo.draft.DraftModuleStore'

        return new_store_list

    if module_store_setting is None:
        return None

    if module_store_setting['default']['ENGINE'] != 'xmodule.modulestore.mixed.MixedModuleStore':
        warnings.warn("Direct access to a modulestore is deprecated. Please use MixedModuleStore.", DeprecationWarning)

        # convert to using mixed module_store
        new_module_store_setting = {
            "default": {
                "ENGINE": "xmodule.modulestore.mixed.MixedModuleStore",
                "OPTIONS": {
                    "mappings": {},
                    "stores": []
                }
            }
        }

        # copy the old configurations into the new settings
        new_module_store_setting['default']['OPTIONS']['stores'] = convert_old_stores_into_list(
            module_store_setting
        )
        module_store_setting = new_module_store_setting

    elif isinstance(module_store_setting['default']['OPTIONS']['stores'], dict):
        warnings.warn(
            "Using a dict for the Stores option in the MixedModuleStore is deprecated.  Please use a list instead.",
            DeprecationWarning
        )

        # convert old-style (unordered) dict to (an ordered) list
        module_store_setting['default']['OPTIONS']['stores'] = convert_old_stores_into_list(
            module_store_setting['default']['OPTIONS']['stores']
        )

        assert isinstance(module_store_setting['default']['OPTIONS']['stores'], list)

    # If Split is not defined but the DraftMongoModuleStore is configured, add Split as a copy of Draft
    mixed_stores = module_store_setting['default']['OPTIONS']['stores']
    is_split_defined = any((store['ENGINE'].endswith('.DraftVersioningModuleStore')) for store in mixed_stores)
    if not is_split_defined:
        # find first setting of mongo store
        mongo_store = next(
            (store for store in mixed_stores if (
                store['ENGINE'].endswith('.DraftMongoModuleStore') or store['ENGINE'].endswith('.DraftModuleStore')
            )),
            None
        )
        if mongo_store:
            # deepcopy mongo -> split
            split_store = copy.deepcopy(mongo_store)
            # update the ENGINE and NAME fields
            split_store['ENGINE'] = 'xmodule.modulestore.split_mongo.split_draft.DraftVersioningModuleStore'
            split_store['NAME'] = 'split'
            # add split to the end of the list
            mixed_stores.append(split_store)

    return module_store_setting


def update_module_store_settings(
        module_store_setting,
        doc_store_settings=None,
        module_store_options=None,
        xml_store_options=None,
):
    """
    Updates the settings for each store defined in the given module_store_setting settings
    with the given doc store configuration and options, overwriting existing keys.
    """
    for store in module_store_setting['default']['OPTIONS']['stores']:
        if store['NAME'] == 'xml':
            xml_store_options and store['OPTIONS'].update(xml_store_options)
        else:
            module_store_options and store['OPTIONS'].update(module_store_options)
            doc_store_settings and store['DOC_STORE_CONFIG'].update(doc_store_settings)
