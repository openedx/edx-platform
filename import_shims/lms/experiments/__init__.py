from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments', 'lms.djangoapps.experiments')

from lms.djangoapps.experiments import *
