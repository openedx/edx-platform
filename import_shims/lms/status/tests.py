from import_shims.warn import warn_deprecated_import

warn_deprecated_import('status.tests', 'common.djangoapps.status.tests')

from common.djangoapps.status.tests import *
