import warnings
warnings.warn("Importing verify_student instead of lms.djangoapps.verify_student is deprecated", stacklevel=2)

from lms.djangoapps.verify_student import *
