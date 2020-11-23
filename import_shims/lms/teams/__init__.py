from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams', 'lms.djangoapps.teams')

from lms.djangoapps.teams import *
