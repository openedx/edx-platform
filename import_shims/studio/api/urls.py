from import_shims.warn import warn_deprecated_import

warn_deprecated_import('api.urls', 'cms.djangoapps.api.urls')

from cms.djangoapps.api.urls import *
