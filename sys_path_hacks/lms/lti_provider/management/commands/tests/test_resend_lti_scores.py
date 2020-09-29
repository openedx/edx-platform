from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'lti_provider.management.commands.tests.test_resend_lti_scores')

from lms.djangoapps.lti_provider.management.commands.tests.test_resend_lti_scores import *
