from import_shims.warn import warn_deprecated_import

warn_deprecated_import('api.apps', 'cms.djangoapps.api.apps')

from cms.djangoapps.api.apps import *
