from import_shims.warn import warn_deprecated_import

warn_deprecated_import('cms_user_tasks.signals', 'cms.djangoapps.cms_user_tasks.signals')

from cms.djangoapps.cms_user_tasks.signals import *
