import warnings
warnings.warn("Importing courseware.course_tools instead of lms.djangoapps.courseware.course_tools is deprecated", stacklevel=2)

from lms.djangoapps.courseware.course_tools import *
