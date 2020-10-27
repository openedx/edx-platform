from import_shims.warn import warn_deprecated_import

warn_deprecated_import('gating', 'lms.djangoapps.gating')

from lms.djangoapps.gating import *
