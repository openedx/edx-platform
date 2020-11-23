from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.services', 'lms.djangoapps.teams.services')

from lms.djangoapps.teams.services import *
