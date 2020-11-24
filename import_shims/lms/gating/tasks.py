from import_shims.warn import warn_deprecated_import

warn_deprecated_import('gating.tasks', 'lms.djangoapps.gating.tasks')

from lms.djangoapps.gating.tasks import *
