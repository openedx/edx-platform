from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.errors', 'lms.djangoapps.teams.errors')

from lms.djangoapps.teams.errors import *
