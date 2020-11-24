from import_shims.warn import warn_deprecated_import

warn_deprecated_import('contentstore.views.export_git', 'cms.djangoapps.contentstore.views.export_git')

from cms.djangoapps.contentstore.views.export_git import *
