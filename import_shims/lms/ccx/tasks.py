from import_shims.warn import warn_deprecated_import

warn_deprecated_import('ccx.tasks', 'lms.djangoapps.ccx.tasks')

from lms.djangoapps.ccx.tasks import *
