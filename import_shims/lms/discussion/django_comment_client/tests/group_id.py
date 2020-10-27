from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'discussion.django_comment_client.tests.group_id')

from lms.djangoapps.discussion.django_comment_client.tests.group_id import *
