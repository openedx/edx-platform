from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.views.tabs', 'cms.djangoapps.contentstore.views.tabs')

from cms.djangoapps.contentstore.views.tabs import *
