from import_shims.warn import warn_deprecated_import

warn_deprecated_import('gating.apps', 'lms.djangoapps.gating.apps')

from lms.djangoapps.gating.apps import *
