from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.management.commands.reindex_course_team')

from lms.djangoapps.teams.management.commands.reindex_course_team import *
