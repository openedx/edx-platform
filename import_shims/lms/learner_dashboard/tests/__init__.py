from import_shims.warn import warn_deprecated_import

warn_deprecated_import('learner_dashboard.tests', 'lms.djangoapps.learner_dashboard.tests')

from lms.djangoapps.learner_dashboard.tests import *
