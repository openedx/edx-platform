from import_shims.warn import warn_deprecated_import

warn_deprecated_import('xblock_config.models', 'cms.djangoapps.xblock_config.models')

from cms.djangoapps.xblock_config.models import *
