from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'courseware.management.commands.dump_course_ids')

from lms.djangoapps.courseware.management.commands.dump_course_ids import *
