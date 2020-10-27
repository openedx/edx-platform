from import_shims.warn import warn_deprecated_import

warn_deprecated_import('badges.api.tests', 'lms.djangoapps.badges.api.tests')

from lms.djangoapps.badges.api.tests import *
