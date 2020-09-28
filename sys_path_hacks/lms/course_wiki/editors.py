import warnings
warnings.warn("Importing course_wiki.editors instead of lms.djangoapps.course_wiki.editors is deprecated", stacklevel=2)

from lms.djangoapps.course_wiki.editors import *
