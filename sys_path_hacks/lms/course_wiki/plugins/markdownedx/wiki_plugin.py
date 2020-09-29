from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('lms.djangoapps', 'course_wiki.plugins.markdownedx.wiki_plugin')

from lms.djangoapps.course_wiki.plugins.markdownedx.wiki_plugin import *
