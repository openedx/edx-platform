import warnings
warnings.warn("Importing course_wiki instead of lms.djangoapps.course_wiki is deprecated", stacklevel=2)

from lms.djangoapps.course_wiki import *
