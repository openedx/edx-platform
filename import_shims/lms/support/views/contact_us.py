from import_shims.warn import warn_deprecated_import

warn_deprecated_import('support.views.contact_us', 'lms.djangoapps.support.views.contact_us')

from lms.djangoapps.support.views.contact_us import *
