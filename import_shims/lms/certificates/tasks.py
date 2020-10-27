from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.tasks', 'lms.djangoapps.certificates.tasks')

from lms.djangoapps.certificates.tasks import *
