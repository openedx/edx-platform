import warnings
warnings.warn("Importing courseware.models instead of lms.djangoapps.courseware.models is deprecated", stacklevel=2)

from lms.djangoapps.courseware.models import *
