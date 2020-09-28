import warnings
warnings.warn("Importing courseware.module_render instead of lms.djangoapps.courseware.module_render is deprecated", stacklevel=2)

from lms.djangoapps.courseware.module_render import *
