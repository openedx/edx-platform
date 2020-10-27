from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.signals', 'lms.djangoapps.discussion.signals')

from lms.djangoapps.discussion.signals import *
