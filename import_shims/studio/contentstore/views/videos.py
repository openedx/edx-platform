from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.views.videos', 'cms.djangoapps.contentstore.views.videos')

from cms.djangoapps.contentstore.views.videos import *
