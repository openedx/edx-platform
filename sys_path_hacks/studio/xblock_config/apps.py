from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'xblock_config.apps')

from cms.djangoapps.xblock_config.apps import *
