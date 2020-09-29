from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.search_indexes')

from lms.djangoapps.teams.search_indexes import *
