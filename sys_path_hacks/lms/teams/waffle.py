from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.waffle')

from lms.djangoapps.teams.waffle import *
