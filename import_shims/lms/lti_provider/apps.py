from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.apps', 'lms.djangoapps.lti_provider.apps')

from lms.djangoapps.lti_provider.apps import *
