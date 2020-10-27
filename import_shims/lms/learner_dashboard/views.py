from import_shims.warn import warn_deprecated_import

warn_deprecated_import('learner_dashboard.views', 'lms.djangoapps.learner_dashboard.views')

from lms.djangoapps.learner_dashboard.views import *
