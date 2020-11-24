from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.views_custom', 'lms.djangoapps.experiments.views_custom')

from lms.djangoapps.experiments.views_custom import *
