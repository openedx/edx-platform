from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.views', 'lms.djangoapps.lti_provider.views')

from lms.djangoapps.lti_provider.views import *
