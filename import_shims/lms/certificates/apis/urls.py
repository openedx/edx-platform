from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.apis.urls', 'lms.djangoapps.certificates.apis.urls')

from lms.djangoapps.certificates.apis.urls import *
