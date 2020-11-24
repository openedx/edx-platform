from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.views.xqueue', 'lms.djangoapps.certificates.views.xqueue')

from lms.djangoapps.certificates.views.xqueue import *
