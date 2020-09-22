import warnings
warnings.warn("Importing course_api.blocks.api instead of lms.djangoapps.course_api.blocks.api is deprecated", stacklevel=2)

from lms.djangoapps.course_api.blocks.api import *
