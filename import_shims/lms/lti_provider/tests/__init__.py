from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.tests', 'lms.djangoapps.lti_provider.tests')

from lms.djangoapps.lti_provider.tests import *
