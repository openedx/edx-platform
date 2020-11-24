from import_shims.warn import warn_deprecated_import

warn_deprecated_import('static_replace.models', 'common.djangoapps.static_replace.models')

from common.djangoapps.static_replace.models import *
