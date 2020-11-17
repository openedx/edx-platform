from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider', 'lms.djangoapps.lti_provider')

from lms.djangoapps.lti_provider import *
