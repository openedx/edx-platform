from import_shims.warn import warn_deprecated_import

warn_deprecated_import('learner_dashboard', 'lms.djangoapps.learner_dashboard')

from lms.djangoapps.learner_dashboard import *
