from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.rest_api.urls', 'cms.djangoapps.contentstore.rest_api.urls')

from cms.djangoapps.contentstore.rest_api.urls import *
