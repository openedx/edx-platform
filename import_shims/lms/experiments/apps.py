from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.apps', 'lms.djangoapps.experiments.apps')

from lms.djangoapps.experiments.apps import *
