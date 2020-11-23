from import_shims.warn import warn_deprecated_import

warn_deprecated_import('cms_user_tasks.apps', 'cms.djangoapps.cms_user_tasks.apps')

from cms.djangoapps.cms_user_tasks.apps import *
