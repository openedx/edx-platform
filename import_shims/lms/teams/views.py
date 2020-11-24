from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.views', 'lms.djangoapps.teams.views')

from lms.djangoapps.teams.views import *
