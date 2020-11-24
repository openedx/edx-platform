from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.plugins', 'lms.djangoapps.teams.plugins')

from lms.djangoapps.teams.plugins import *
