from import_shims.warn import warn_deprecated_import

warn_deprecated_import('tests', 'lms.djangoapps.tests')

from lms.djangoapps.tests import *
