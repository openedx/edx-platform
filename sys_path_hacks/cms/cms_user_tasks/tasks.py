from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('cms.djangoapps', 'cms_user_tasks.tasks')

from cms.djangoapps.cms_user_tasks.tasks import *
