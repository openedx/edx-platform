from import_shims.warn import warn_deprecated_import

warn_deprecated_import('support.views.manage_user', 'lms.djangoapps.support.views.manage_user')

from lms.djangoapps.support.views.manage_user import *
