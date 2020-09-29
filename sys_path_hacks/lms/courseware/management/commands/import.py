from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.management.commands.import')

from lms.djangoapps.courseware.management.commands.import import *
