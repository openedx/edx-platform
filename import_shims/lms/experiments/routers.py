from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.routers', 'lms.djangoapps.experiments.routers')

from lms.djangoapps.experiments.routers import *
