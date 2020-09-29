from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'bulk_email.models_api')

from lms.djangoapps.bulk_email.models_api import *
