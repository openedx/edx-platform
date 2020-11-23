from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.models', 'lms.djangoapps.lti_provider.models')

from lms.djangoapps.lti_provider.models import *
