from import_shims.warn import warn_deprecated_import

warn_deprecated_import('util.tests', 'common.djangoapps.util.tests')

from common.djangoapps.util.tests import *
