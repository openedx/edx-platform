from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.management', 'lms.djangoapps.lti_provider.management')

from lms.djangoapps.lti_provider.management import *
