from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.rest_api', 'cms.djangoapps.contentstore.rest_api')

from cms.djangoapps.contentstore.rest_api import *
