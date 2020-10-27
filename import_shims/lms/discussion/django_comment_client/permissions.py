from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.django_comment_client.permissions')

from lms.djangoapps.discussion.django_comment_client.permissions import *
