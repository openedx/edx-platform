from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.outcomes', 'lms.djangoapps.lti_provider.outcomes')

from lms.djangoapps.lti_provider.outcomes import *
