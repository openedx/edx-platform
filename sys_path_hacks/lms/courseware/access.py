import warnings
warnings.warn("Importing courseware.access instead of lms.djangoapps.courseware.access is deprecated", stacklevel=2)

from lms.djangoapps.courseware.access import *
