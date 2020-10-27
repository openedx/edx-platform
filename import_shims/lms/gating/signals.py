from import_shims.warn import warn_deprecated_import

warn_deprecated_import('gating.signals', 'lms.djangoapps.gating.signals')

from lms.djangoapps.gating.signals import *
