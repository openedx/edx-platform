from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.admin')

from lms.djangoapps.teams.admin import *
