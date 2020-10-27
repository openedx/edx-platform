from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.permissions', 'lms.djangoapps.experiments.permissions')

from lms.djangoapps.experiments.permissions import *
