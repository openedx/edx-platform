import warnings
warnings.warn("Importing courseware.permissions instead of lms.djangoapps.courseware.permissions is deprecated", stacklevel=2)

from lms.djangoapps.courseware.permissions import *
