from import_shims.warn import warn_deprecated_import

warn_deprecated_import('courseware.management.commands.dump_course_structure', 'lms.djangoapps.courseware.management.commands.dump_course_structure')

from lms.djangoapps.courseware.management.commands.dump_course_structure import *
