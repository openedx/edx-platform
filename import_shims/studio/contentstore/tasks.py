from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.tasks', 'cms.djangoapps.contentstore.tasks')

from cms.djangoapps.contentstore.tasks import *
