import warnings
warnings.warn("Importing course_blocks instead of lms.djangoapps.course_blocks is deprecated", stacklevel=2)

from lms.djangoapps.course_blocks import *
