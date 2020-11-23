from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lti_provider.management.commands.tests', 'lms.djangoapps.lti_provider.management.commands.tests')

from lms.djangoapps.lti_provider.management.commands.tests import *
