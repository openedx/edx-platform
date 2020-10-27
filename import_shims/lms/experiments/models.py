from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.models', 'lms.djangoapps.experiments.models')

from lms.djangoapps.experiments.models import *
