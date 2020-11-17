from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.users', 'lms.djangoapps.lti_provider.users')

from lms.djangoapps.lti_provider.users import *
