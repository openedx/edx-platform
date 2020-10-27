from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.admin', 'lms.djangoapps.teams.admin')

from lms.djangoapps.teams.admin import *
