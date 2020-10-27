from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'lti_provider.models')

from lms.djangoapps.lti_provider.models import *
