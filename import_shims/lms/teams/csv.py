from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.csv', 'lms.djangoapps.teams.csv')

from lms.djangoapps.teams.csv import *
