from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.storage', 'cms.djangoapps.contentstore.storage')

from cms.djangoapps.contentstore.storage import *
