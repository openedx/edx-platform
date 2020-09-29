from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.csv')

from lms.djangoapps.teams.csv import *
