import warnings
warnings.warn("Importing course_wiki.settings instead of lms.djangoapps.course_wiki.settings is deprecated", stacklevel=2)

from lms.djangoapps.course_wiki.settings import *
