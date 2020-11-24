from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.views.course', 'cms.djangoapps.contentstore.views.course')

from cms.djangoapps.contentstore.views.course import *
