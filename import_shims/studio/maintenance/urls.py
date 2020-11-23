from import_shims.warn import warn_deprecated_import

warn_deprecated_import('maintenance.urls', 'cms.djangoapps.maintenance.urls')

from cms.djangoapps.maintenance.urls import *
