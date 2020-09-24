import warnings
warnings.warn("Importing courseware.views.index instead of lms.djangoapps.courseware.views.index is deprecated", stacklevel=2)

from lms.djangoapps.courseware.views.index import *
