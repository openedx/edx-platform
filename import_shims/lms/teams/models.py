from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.models', 'lms.djangoapps.teams.models')

from lms.djangoapps.teams.models import *
