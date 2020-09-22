import warnings
warnings.warn("Importing course_blocks.api instead of lms.djangoapps.course_blocks.api is deprecated", stacklevel=2)

from lms.djangoapps.course_blocks.api import *
