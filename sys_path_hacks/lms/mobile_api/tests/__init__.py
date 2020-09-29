from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'mobile_api.tests')

from lms.djangoapps.mobile_api.tests import *
