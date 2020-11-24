from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.file', 'common.djangoapps.util.file')

from common.djangoapps.util.file import *
