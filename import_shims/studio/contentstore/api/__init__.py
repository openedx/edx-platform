from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.api', 'cms.djangoapps.contentstore.api')

from cms.djangoapps.contentstore.api import *
