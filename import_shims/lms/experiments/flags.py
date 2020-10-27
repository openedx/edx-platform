from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.flags', 'lms.djangoapps.experiments.flags')

from lms.djangoapps.experiments.flags import *
