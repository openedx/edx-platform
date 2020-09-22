import warnings
warnings.warn("Importing courseware.fields instead of lms.djangoapps.courseware.fields is deprecated", stacklevel=2)

from lms.djangoapps.courseware.fields import *
