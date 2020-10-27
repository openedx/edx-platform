from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.management', 'lms.djangoapps.teams.management')

from lms.djangoapps.teams.management import *
