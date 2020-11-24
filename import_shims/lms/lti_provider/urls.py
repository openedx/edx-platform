from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.urls', 'lms.djangoapps.lti_provider.urls')

from lms.djangoapps.lti_provider.urls import *
