from import_shims.warn import warn_deprecated_import

warn_deprecated_import('gating.tests', 'lms.djangoapps.gating.tests')

from lms.djangoapps.gating.tests import *
