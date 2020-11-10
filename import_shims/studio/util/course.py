from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.course', 'common.djangoapps.util.course')

from common.djangoapps.util.course import *
