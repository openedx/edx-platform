from import_shims.warn import warn_deprecated_import

warn_deprecated_import('xblock_config.admin', 'cms.djangoapps.xblock_config.admin')

from cms.djangoapps.xblock_config.admin import *
