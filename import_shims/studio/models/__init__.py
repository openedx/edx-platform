from import_shims.warn import warn_deprecated_import

warn_deprecated_import('models', 'cms.djangoapps.models')

from cms.djangoapps.models import *
