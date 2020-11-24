from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.apis', 'lms.djangoapps.certificates.apis')

from lms.djangoapps.certificates.apis import *
