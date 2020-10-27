from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'teams.waffle')

# pylint: disable=wildcard-import
from lms.djangoapps.teams.toggles import *
