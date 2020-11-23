from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.filters', 'lms.djangoapps.experiments.filters')

from lms.djangoapps.experiments.filters import *
