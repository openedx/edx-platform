from import_shims.warn import warn_deprecated_import

warn_deprecated_import('teams.waffle', 'lms.djangoapps.teams.waffle')

# pylint: disable=wildcard-import
from lms.djangoapps.teams.toggles import *
