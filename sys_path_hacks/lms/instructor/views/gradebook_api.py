import warnings
warnings.warn("Importing instructor.views.gradebook_api instead of lms.djangoapps.instructor.views.gradebook_api is deprecated", stacklevel=2)

from lms.djangoapps.instructor.views.gradebook_api import *
