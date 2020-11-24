from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.testing', 'common.djangoapps.util.testing')

from common.djangoapps.util.testing import *
