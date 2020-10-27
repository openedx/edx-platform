from import_shims.warn import warn_deprecated_import

warn_deprecated_import('cms_user_tasks.tasks', 'cms.djangoapps.cms_user_tasks.tasks')

from cms.djangoapps.cms_user_tasks.tasks import *
