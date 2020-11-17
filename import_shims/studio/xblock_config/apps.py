from import_shims.warn import warn_deprecated_import

warn_deprecated_import('xblock_config.apps', 'cms.djangoapps.xblock_config.apps')

from cms.djangoapps.xblock_config.apps import *
