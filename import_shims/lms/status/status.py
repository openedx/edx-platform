from import_shims.warn import warn_deprecated_import

warn_deprecated_import('status.status', 'common.djangoapps.status.status')

from common.djangoapps.status.status import *
