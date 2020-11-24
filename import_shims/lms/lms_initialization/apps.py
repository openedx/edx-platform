from import_shims.warn import warn_deprecated_import

warn_deprecated_import('lms_initialization.apps', 'lms.djangoapps.lms_initialization.apps')

from lms.djangoapps.lms_initialization.apps import *
