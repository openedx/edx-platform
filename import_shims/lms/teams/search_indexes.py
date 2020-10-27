from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.search_indexes', 'lms.djangoapps.teams.search_indexes')

from lms.djangoapps.teams.search_indexes import *
