from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.admin', 'lms.djangoapps.experiments.admin')

from lms.djangoapps.experiments.admin import *
