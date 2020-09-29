from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'certificates.management.commands.resubmit_error_certificates')

from lms.djangoapps.certificates.management.commands.resubmit_error_certificates import *
