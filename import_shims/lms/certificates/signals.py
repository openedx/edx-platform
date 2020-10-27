from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.signals')

from lms.djangoapps.certificates.signals import *
