from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.views.import_export', 'cms.djangoapps.contentstore.views.import_export')

from cms.djangoapps.contentstore.views.import_export import *
