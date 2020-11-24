from import_shims.warn import warn_deprecated_import

warn_deprecated_import('experiments.tests', 'lms.djangoapps.experiments.tests')

from lms.djangoapps.experiments.tests import *
