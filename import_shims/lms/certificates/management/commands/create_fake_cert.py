from import_shims.warn import warn_deprecated_import

warn_deprecated_import('certificates.management.commands.create_fake_cert', 'lms.djangoapps.certificates.management.commands.create_fake_cert')

from lms.djangoapps.certificates.management.commands.create_fake_cert import *
