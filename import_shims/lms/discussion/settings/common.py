from import_shims.warn import warn_deprecated_import

warn_deprecated_import('discussion.settings.common', 'lms.djangoapps.discussion.settings.common')

from lms.djangoapps.discussion.settings.common import *
