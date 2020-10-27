from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'mailing.management.commands')

from lms.djangoapps.mailing.management.commands import *
