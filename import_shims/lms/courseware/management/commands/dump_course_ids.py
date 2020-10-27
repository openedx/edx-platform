from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.management.commands.dump_course_ids', 'lms.djangoapps.courseware.management.commands.dump_course_ids')

from lms.djangoapps.courseware.management.commands.dump_course_ids import *
