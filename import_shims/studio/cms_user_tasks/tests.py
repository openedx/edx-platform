from import_shims.warn import warn_deprecated_import

warn_deprecated_import('cms_user_tasks.tests', 'cms.djangoapps.cms_user_tasks.tests')

from cms.djangoapps.cms_user_tasks.tests import *
