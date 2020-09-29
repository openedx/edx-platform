from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'commerce.signals')

from lms.djangoapps.commerce.signals import *
