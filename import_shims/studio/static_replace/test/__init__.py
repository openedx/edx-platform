from import_shims.warn import warn_deprecated_import

warn_deprecated_import('static_replace.test', 'common.djangoapps.static_replace.test')

from common.djangoapps.static_replace.test import *
