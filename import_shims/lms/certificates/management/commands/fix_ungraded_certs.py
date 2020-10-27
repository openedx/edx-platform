from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.management.commands.fix_ungraded_certs')

from lms.djangoapps.certificates.management.commands.fix_ungraded_certs import *
