from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.models', 'cms.djangoapps.contentstore.models')

from cms.djangoapps.contentstore.models import *
