from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.management.commands.assign_roles_for_course')

from lms.djangoapps.discussion.management.commands.assign_roles_for_course import *
