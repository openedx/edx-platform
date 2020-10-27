from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.admin', 'lms.djangoapps.lti_provider.admin')

from lms.djangoapps.lti_provider.admin import *
