from import_shims.warn import warn_deprecated_import

warn_deprecated_import('static_replace.admin', 'common.djangoapps.static_replace.admin')

from common.djangoapps.static_replace.admin import *
