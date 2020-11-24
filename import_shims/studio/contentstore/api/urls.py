from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.api.urls', 'cms.djangoapps.contentstore.api.urls')

from cms.djangoapps.contentstore.api.urls import *
