import warnings
warnings.warn("Importing verify_student.services instead of lms.djangoapps.verify_student.services is deprecated", stacklevel=2)

from lms.djangoapps.verify_student.services import *
