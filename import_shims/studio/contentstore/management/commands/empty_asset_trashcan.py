from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'contentstore.management.commands.empty_asset_trashcan')

from cms.djangoapps.contentstore.management.commands.empty_asset_trashcan import *
