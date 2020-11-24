from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.urls', 'lms.djangoapps.experiments.urls')

from lms.djangoapps.experiments.urls import *
