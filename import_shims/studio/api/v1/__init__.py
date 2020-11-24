from import_shims.warn import warn_deprecated_import

warn_deprecated_import('api.v1', 'cms.djangoapps.api.v1')

from cms.djangoapps.api.v1 import *
