from import_shims.warn import warn_deprecated_import

warn_deprecated_import('branding.api_urls', 'lms.djangoapps.branding.api_urls')

from lms.djangoapps.branding.api_urls import *
