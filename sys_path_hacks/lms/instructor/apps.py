import warnings
warnings.warn("Importing instructor.apps instead of lms.djangoapps.instructor.apps is deprecated", stacklevel=2)

from lms.djangoapps.instructor.apps import *
