from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.models')

from lms.djangoapps.commerce.models import *
