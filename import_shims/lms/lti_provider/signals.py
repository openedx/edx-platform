from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.signals', 'lms.djangoapps.lti_provider.signals')

from lms.djangoapps.lti_provider.signals import *
