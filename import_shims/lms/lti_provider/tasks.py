from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.tasks', 'lms.djangoapps.lti_provider.tasks')

from lms.djangoapps.lti_provider.tasks import *
