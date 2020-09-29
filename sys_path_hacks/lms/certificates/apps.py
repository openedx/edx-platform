from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.apps')

from lms.djangoapps.certificates.apps import *
