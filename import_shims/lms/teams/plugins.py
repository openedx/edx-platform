from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.plugins')

from lms.djangoapps.teams.plugins import *
