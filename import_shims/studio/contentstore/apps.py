from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.apps', 'cms.djangoapps.contentstore.apps')

from cms.djangoapps.contentstore.apps import *
