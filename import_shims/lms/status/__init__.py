from import_shims.warn import warn_deprecated_import

warn_deprecated_import('status', 'common.djangoapps.status')

from common.djangoapps.status import *
