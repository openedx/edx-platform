from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_wiki.plugins.markdownedx.mdx_video')

from lms.djangoapps.course_wiki.plugins.markdownedx.mdx_video import *
