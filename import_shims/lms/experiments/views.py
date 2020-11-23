from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.views', 'lms.djangoapps.experiments.views')

from lms.djangoapps.experiments.views import *
