from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.models')

from lms.djangoapps.certificates.models import *
