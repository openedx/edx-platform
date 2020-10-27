from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.admin', 'cms.djangoapps.contentstore.admin')

from cms.djangoapps.contentstore.admin import *
