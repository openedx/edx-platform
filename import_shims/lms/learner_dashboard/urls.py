from import_shims.warn import warn_deprecated_import

warn_deprecated_import('learner_dashboard.urls', 'lms.djangoapps.learner_dashboard.urls')

from lms.djangoapps.learner_dashboard.urls import *
