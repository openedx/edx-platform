from import_shims.warn import warn_deprecated_import

warn_deprecated_import('dashboard.tests', 'lms.djangoapps.dashboard.tests')

from lms.djangoapps.dashboard.tests import *
