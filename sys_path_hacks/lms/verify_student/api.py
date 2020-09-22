import warnings
warnings.warn("Importing verify_student.api instead of lms.djangoapps.verify_student.api is deprecated", stacklevel=2)

from lms.djangoapps.verify_student.api import *
