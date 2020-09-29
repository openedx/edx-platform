from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.management')

from lms.djangoapps.certificates.management import *
