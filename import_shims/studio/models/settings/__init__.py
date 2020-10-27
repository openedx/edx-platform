from import_shims.warn import warn_deprecated_import

warn_deprecated_import('models.settings', 'cms.djangoapps.models.settings')

from cms.djangoapps.models.settings import *
