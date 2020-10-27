from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.views.webview', 'lms.djangoapps.certificates.views.webview')

from lms.djangoapps.certificates.views.webview import *
