import warnings
warnings.warn("Importing course_wiki.plugins instead of lms.djangoapps.course_wiki.plugins is deprecated", stacklevel=2)

from lms.djangoapps.course_wiki.plugins import *
