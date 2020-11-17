from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.views.library', 'cms.djangoapps.contentstore.views.library')

from cms.djangoapps.contentstore.views.library import *
