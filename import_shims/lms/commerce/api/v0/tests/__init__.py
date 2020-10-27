from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.api.v0.tests')

from lms.djangoapps.commerce.api.v0.tests import *
