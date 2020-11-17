from import_shims.warn import warn_deprecated_import

warn_deprecated_import('gating.api', 'lms.djangoapps.gating.api')

from lms.djangoapps.gating.api import *
