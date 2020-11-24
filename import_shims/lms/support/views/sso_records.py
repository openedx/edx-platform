from import_shims.warn import warn_deprecated_import

warn_deprecated_import('support.views.sso_records', 'lms.djangoapps.support.views.sso_records')

from lms.djangoapps.support.views.sso_records import *
