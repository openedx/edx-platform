from import_shims.warn import warn_deprecated_import

warn_deprecated_import('branding.api', 'lms.djangoapps.branding.api')

from lms.djangoapps.branding.api import *
