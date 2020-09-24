import warnings
warnings.warn("Importing course_wiki.middleware instead of lms.djangoapps.course_wiki.middleware is deprecated", stacklevel=2)

from lms.djangoapps.course_wiki.middleware import *
