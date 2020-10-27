from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.factories', 'lms.djangoapps.experiments.factories')

from lms.djangoapps.experiments.factories import *
