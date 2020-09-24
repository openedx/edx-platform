import warnings
warnings.warn("Importing course_api.blocks instead of lms.djangoapps.course_api.blocks is deprecated", stacklevel=2)

from lms.djangoapps.course_api.blocks import *
