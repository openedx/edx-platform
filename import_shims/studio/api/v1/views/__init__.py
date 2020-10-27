from import_shims.warn import warn_deprecated_import

warn_deprecated_import('api.v1.views', 'cms.djangoapps.api.v1.views')

from cms.djangoapps.api.v1.views import *
