import warnings
warnings.warn("Importing instructor.views.api instead of lms.djangoapps.instructor.views.api is deprecated", stacklevel=2)

from lms.djangoapps.instructor.views.api import *
