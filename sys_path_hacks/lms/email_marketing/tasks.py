from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'email_marketing.tasks')

from lms.djangoapps.email_marketing.tasks import *
