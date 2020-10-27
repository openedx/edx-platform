from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.stable_bucketing', 'lms.djangoapps.experiments.stable_bucketing')

from lms.djangoapps.experiments.stable_bucketing import *
