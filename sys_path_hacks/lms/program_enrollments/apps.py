import warnings
warnings.warn("Importing program_enrollments.apps instead of lms.djangoapps.program_enrollments.apps is deprecated", stacklevel=2)

from lms.djangoapps.program_enrollments.apps import *
