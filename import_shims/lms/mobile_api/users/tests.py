from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'mobile_api.users.tests')

from lms.djangoapps.mobile_api.users.tests import *
